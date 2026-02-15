import logging
import os
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Index, LargeBinary, String, create_engine, func, select
from sqlalchemy.orm import Mapped, Session, declarative_base, mapped_column

from infrastructure.config.env_loader import ensure_env_loaded

logger = logging.getLogger(__name__)
Base = declarative_base()


class DatabaseStorageError(RuntimeError):
    """Raised when required DB file storage operation fails."""


class StoredFile(Base):
    __tablename__ = "stored_files"
    __table_args__ = (
        Index("idx_stored_files_kind_filename", "kind", "filename", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_brand: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


def _to_meta_dict(entity: StoredFile) -> dict[str, Any]:
    return {
        "id": entity.id,
        "kind": entity.kind,
        "filename": entity.filename,
        "mime_type": entity.mime_type,
        "source_brand": entity.source_brand,
        "created_at": entity.created_at.isoformat() if entity.created_at else None,
    }


def _to_full_dict(entity: StoredFile) -> dict[str, Any]:
    data = _to_meta_dict(entity)
    data["content"] = entity.content
    return data


def _get_dsn() -> Optional[str]:
    ensure_env_loaded()
    return os.getenv("POSTGRES_DSN")


def _get_engine():
    dsn = _get_dsn()
    if not dsn:
        return None
    return create_engine(dsn, future=True, pool_pre_ping=True)


def _ensure_schema(engine) -> None:
    Base.metadata.create_all(engine)


def store_file_if_configured(
    *,
    kind: str,
    filename: str,
    content: bytes,
    mime_type: str = "application/octet-stream",
    source_brand: str | None = None,
) -> bool:
    """Persist file bytes to PostgreSQL if POSTGRES_DSN is configured."""
    engine = _get_engine()
    if engine is None:
        logger.debug("DB storage disabled: POSTGRES_DSN is not configured.")
        return False

    try:
        _ensure_schema(engine)
        with Session(engine) as session:
            session.add(
                StoredFile(
                    kind=kind,
                    filename=filename,
                    mime_type=mime_type,
                    source_brand=source_brand,
                    content=content,
                )
            )
            session.commit()
        return True
    except Exception as exc:
        logger.warning("DB storage failed for '%s' (%s).", filename, exc)
        return False


def list_files_if_configured(limit: int = 200) -> list[dict[str, Any]]:
    """Return latest stored files metadata or empty list when DB is unavailable."""
    engine = _get_engine()
    if engine is None:
        logger.debug("DB listing disabled: POSTGRES_DSN is not configured.")
        return []

    try:
        _ensure_schema(engine)
        stmt = select(StoredFile).order_by(StoredFile.id.desc()).limit(limit)
        with Session(engine) as session:
            rows = session.scalars(stmt).all()
        return [_to_meta_dict(row) for row in rows]
    except Exception as exc:
        logger.warning("DB listing failed: %s", exc)
        return []


def get_file_if_configured(file_id: int) -> dict[str, Any] | None:
    """Return stored file by id or None when not found/DB unavailable."""
    engine = _get_engine()
    if engine is None:
        logger.debug("DB read disabled: POSTGRES_DSN is not configured.")
        return None

    try:
        _ensure_schema(engine)
        stmt = select(StoredFile).where(StoredFile.id == file_id).limit(1)
        with Session(engine) as session:
            row = session.scalars(stmt).first()
        return _to_full_dict(row) if row else None
    except Exception as exc:
        logger.warning("DB read failed for id=%s: %s", file_id, exc)
        return None


def list_files_filtered_if_configured(
    *,
    limit: int = 200,
    kind: str | None = None,
    source_brand: str | None = None,
    filename_contains: str | None = None,
) -> list[dict[str, Any]]:
    """Return filtered files metadata or empty list when DB is unavailable."""
    engine = _get_engine()
    if engine is None:
        logger.debug("DB listing disabled: POSTGRES_DSN is not configured.")
        return []

    try:
        _ensure_schema(engine)
        stmt = select(StoredFile)
        if kind:
            stmt = stmt.where(StoredFile.kind == kind)
        if source_brand:
            stmt = stmt.where(StoredFile.source_brand == source_brand)
        if filename_contains:
            stmt = stmt.where(StoredFile.filename.ilike(f"%{filename_contains}%"))
        stmt = stmt.order_by(StoredFile.id.desc()).limit(limit)
        with Session(engine) as session:
            rows = session.scalars(stmt).all()
        return [_to_meta_dict(row) for row in rows]
    except Exception as exc:
        logger.warning("DB filtered listing failed: %s", exc)
        return []


def get_latest_file_by_name_if_configured(kind: str, filename: str) -> dict[str, Any] | None:
    """Return latest file by kind+filename or None."""
    engine = _get_engine()
    if engine is None:
        return None

    try:
        _ensure_schema(engine)
        stmt = (
            select(StoredFile)
            .where(StoredFile.kind == kind, StoredFile.filename == filename)
            .order_by(StoredFile.id.desc())
            .limit(1)
        )
        with Session(engine) as session:
            row = session.scalars(stmt).first()
        return _to_full_dict(row) if row else None
    except Exception:
        return None

