import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, create_engine, func, select, text
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column, relationship

from application.dto.quotation_request import QuotationRequest
from infrastructure.config.env_loader import ensure_env_loaded

logger = logging.getLogger(__name__)
Base = declarative_base()


class QuotationRun(Base):
    __tablename__ = "quotation_runs"
    __table_args__ = (
        Index("idx_quotation_runs_output_filename", "output_filename", "created_at"),
        Index("idx_quotation_runs_brand", "brand", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    client_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    input_filename: Mapped[str] = mapped_column(String, nullable=False)
    output_filename: Mapped[str] = mapped_column(String, nullable=False)
    markup: Mapped[float] = mapped_column(nullable=False)
    discount: Mapped[float] = mapped_column(nullable=False)
    euro: Mapped[float] = mapped_column(nullable=False)
    for_client: Mapped[bool] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="done")
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    lines: Mapped[list["QuotationLine"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
    )


class QuotationLine(Base):
    __tablename__ = "quotation_lines"
    __table_args__ = (
        Index("idx_quotation_lines_run_line_no", "run_id", "line_no"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("quotation_runs.id", ondelete="CASCADE"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    input_code: Mapped[str] = mapped_column(String, nullable=False)
    quantity: Mapped[str] = mapped_column(String, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)

    run: Mapped[QuotationRun] = relationship(back_populates="lines")


def _get_engine():
    ensure_env_loaded()
    dsn = os.getenv("POSTGRES_DSN")
    if not dsn:
        return None
    return create_engine(dsn, future=True, pool_pre_ping=True)


def _ensure_schema(engine) -> None:
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE quotation_runs ADD COLUMN IF NOT EXISTS client_name VARCHAR"))


def _value_from_list(data: dict[str, list], key: str, idx: int) -> Any:
    values = data.get(key) or []
    return values[idx] if idx < len(values) else None


def _build_generic_line_payload(data: dict[str, list], idx: int) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "Code": _value_from_list(data, "codes", idx),
        "Quantity": _value_from_list(data, "qty", idx),
    }
    optional_keys = {
        "SupplierCode": "samasz_codes",
        "Price": "prices",
        "MonthlyPrice": "monthly_prices",
        "WeeklyPrice": "weekly_prices",
        "ClientPrice": "prices_for_client",
        "ClientWeeklyPrice": "prices_for_client_weekly",
        "ClientMonthlyPrice": "prices_for_client_monthly",
    }
    for out_key, in_key in optional_keys.items():
        value = _value_from_list(data, in_key, idx)
        if value is not None:
            payload[out_key] = value
    return payload


def save_generic_quotation_if_configured(
    request: QuotationRequest,
    output_filename: str,
    data: dict[str, list],
) -> int | None:
    engine = _get_engine()
    if engine is None:
        return None

    try:
        _ensure_schema(engine)
        codes = data.get("codes") or []
        qty = data.get("qty") or []
        with Session(engine) as session:
            run = QuotationRun(
                brand=request.brand,
                client_name=request.client_name or None,
                input_filename=request.filename,
                output_filename=output_filename,
                markup=request.markup,
                discount=request.discount,
                euro=request.euro,
                for_client=request.for_client,
                status="done",
            )
            session.add(run)
            session.flush()

            max_len = max(len(codes), len(qty))
            for idx in range(max_len):
                input_code = str(codes[idx]) if idx < len(codes) else ""
                quantity = str(qty[idx]) if idx < len(qty) else ""
                payload = _build_generic_line_payload(data, idx)
                session.add(
                    QuotationLine(
                        run_id=run.id,
                        line_no=idx,
                        input_code=input_code,
                        quantity=quantity,
                        payload_json=json.dumps(payload, ensure_ascii=False),
                    )
                )
            session.commit()
            return run.id
    except Exception as exc:
        logger.warning("Saving generic quotation run failed: %s", exc)
        return None


def save_kv_quotation_if_configured(
    request: QuotationRequest,
    output_filename: str,
    codes: list,
    qty: list,
    prices: list,
    client_prices: list | None,
) -> int | None:
    engine = _get_engine()
    if engine is None:
        return None

    try:
        _ensure_schema(engine)
        with Session(engine) as session:
            run = QuotationRun(
                brand=request.brand,
                client_name=request.client_name or None,
                input_filename=request.filename,
                output_filename=output_filename,
                markup=request.markup,
                discount=request.discount,
                euro=request.euro,
                for_client=request.for_client,
                status="done",
            )
            session.add(run)
            session.flush()

            prices_for_client = client_prices or []
            max_len = max(len(codes), len(qty), len(prices), len(prices_for_client))
            for idx in range(max_len):
                code = str(codes[idx]) if idx < len(codes) else ""
                quantity = str(qty[idx]) if idx < len(qty) else ""
                price = prices[idx] if idx < len(prices) else None
                client_price = prices_for_client[idx] if idx < len(prices_for_client) else None
                payload = {"Code": code, "Quantity": quantity, "Price": price}
                if client_price is not None:
                    payload["ClientPrice"] = client_price
                session.add(
                    QuotationLine(
                        run_id=run.id,
                        line_no=idx,
                        input_code=code,
                        quantity=quantity,
                        payload_json=json.dumps(payload, ensure_ascii=False),
                    )
                )
            session.commit()
            return run.id
    except Exception as exc:
        logger.warning("Saving KV quotation run failed: %s", exc)
        return None


def get_latest_run_id_by_output_filename_if_configured(output_filename: str) -> int | None:
    engine = _get_engine()
    if engine is None:
        return None
    try:
        _ensure_schema(engine)
        stmt = (
            select(QuotationRun.id)
            .where(QuotationRun.output_filename == output_filename)
            .order_by(QuotationRun.id.desc())
            .limit(1)
        )
        with Session(engine) as session:
            row = session.execute(stmt).first()
        return int(row[0]) if row else None
    except Exception as exc:
        logger.warning("Fetching latest run id failed: %s", exc)
        return None


def get_run_with_lines_if_configured(run_id: int) -> dict[str, Any] | None:
    engine = _get_engine()
    if engine is None:
        return None
    try:
        _ensure_schema(engine)
        with Session(engine) as session:
            run = session.get(QuotationRun, run_id)
            if not run:
                return None
            lines_stmt = (
                select(QuotationLine)
                .where(QuotationLine.run_id == run_id)
                .order_by(QuotationLine.line_no.asc())
            )
            lines = session.scalars(lines_stmt).all()

        return {
            "id": run.id,
            "brand": run.brand,
            "client_name": run.client_name,
            "input_filename": run.input_filename,
            "output_filename": run.output_filename,
            "markup": run.markup,
            "discount": run.discount,
            "euro": run.euro,
            "for_client": run.for_client,
            "status": run.status,
            "created_at": run.created_at,
            "lines": [
                {
                    "line_no": line.line_no,
                    "input_code": line.input_code,
                    "quantity": line.quantity,
                    "payload": json.loads(line.payload_json),
                }
                for line in lines
            ],
        }
    except Exception as exc:
        logger.warning("Fetching run with lines failed: %s", exc)
        return None


def list_runs_if_configured(
    *,
    limit: int = 200,
    brand: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    engine = _get_engine()
    if engine is None:
        return []
    try:
        _ensure_schema(engine)
        stmt = select(QuotationRun)
        if brand:
            stmt = stmt.where(QuotationRun.brand == brand)
        if status:
            stmt = stmt.where(QuotationRun.status == status)
        stmt = stmt.order_by(QuotationRun.id.desc()).limit(limit)
        with Session(engine) as session:
            rows = session.scalars(stmt).all()
        return [
            {
                "id": row.id,
                "brand": row.brand,
                "client_name": row.client_name,
                "input_filename": row.input_filename,
                "output_filename": row.output_filename,
                "markup": row.markup,
                "discount": row.discount,
                "euro": row.euro,
                "for_client": row.for_client,
                "status": row.status,
                "error_message": row.error_message,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    except Exception as exc:
        logger.warning("Listing runs failed: %s", exc)
        return []


def get_run_meta_if_configured(run_id: int) -> dict[str, Any] | None:
    engine = _get_engine()
    if engine is None:
        return None
    try:
        _ensure_schema(engine)
        with Session(engine) as session:
            run = session.get(QuotationRun, run_id)
            if not run:
                return None
        return {
            "id": run.id,
            "brand": run.brand,
            "client_name": run.client_name,
            "input_filename": run.input_filename,
            "output_filename": run.output_filename,
            "markup": run.markup,
            "discount": run.discount,
            "euro": run.euro,
            "for_client": run.for_client,
            "status": run.status,
            "error_message": run.error_message,
            "created_at": run.created_at.isoformat() if run.created_at else None,
        }
    except Exception as exc:
        logger.warning("Getting run meta failed: %s", exc)
        return None
