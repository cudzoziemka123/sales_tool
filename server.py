import io
import os
import uuid
from pathlib import Path

import pandas as pd
from flask import Flask, abort, g, jsonify, render_template, request, send_file
from sqlalchemy import create_engine, text
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from werkzeug.utils import secure_filename
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException as SeleniumTimeoutException,
    WebDriverException,
)

from application.dto.quotation_request import InvalidQuotationRequestError, QuotationRequest
from application.errors import (
    AppError,
    ConfigAppError,
    ExternalServiceAppError,
    ExternalTimeoutAppError,
    NotFoundAppError,
    StorageAppError,
    UploadTooLargeAppError,
)
from infrastructure.config.env_loader import MissingEnvVarError, ensure_env_loaded
from infrastructure.db.quotation_data_store import (
    get_latest_run_id_by_output_filename_if_configured,
    get_run_meta_if_configured,
    get_run_with_lines_if_configured,
    list_runs_if_configured,
)
from infrastructure.db.postgres_file_store import (
    DatabaseStorageError,
    get_file_if_configured,
    list_files_filtered_if_configured,
    store_file_if_configured,
)
from presentation.bootstrap import get_dispatcher

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB
ensure_env_loaded()

_DISPATCHER = get_dispatcher()
_REQUIRED_INPUT_COLUMNS = ("Code", "Qty")
_LOCAL_INPUT_DIR = Path("from_client")
_LOCAL_OUTPUT_DIR = Path("for_client")
_REQUIRED_ENV_KEYS = (
    "SAMASZ_COMPANY",
    "SAMASZ_LOGIN",
    "SAMASZ_PASSWORD",
    "KRONE_LOGIN",
    "KRONE_PASSWORD",
    "KV_LOGIN",
    "KV_PASSWORD",
    "PARTS_LOGIN",
    "PARTS_PASSWORD",
)

_ERROR_USER_MESSAGES = {
    "ERR_INVALID_QUOTATION_REQUEST": "Nieprawidlowe dane formularza lub pliku.",
    "ERR_UPLOAD_TOO_LARGE": "Plik jest za duzy. Maksymalny rozmiar to 10 MB.",
    "ERR_CONFIG": "Brak wymaganej konfiguracji srodowiska.",
    "ERR_STORAGE": "Wystapil blad zapisu/odczytu danych.",
    "ERR_NOT_FOUND": "Nie znaleziono zasobu.",
    "ERR_EXTERNAL_SERVICE": "Blad uslugi zewnetrznej (integracja scrapera).",
    "ERR_EXTERNAL_TIMEOUT": "Przekroczono czas oczekiwania na odpowiedz uslugi zewnetrznej.",
    "ERR_HTTP_413": "Plik jest za duzy.",
    "ERR_HTTP_404": "Nie znaleziono zasobu.",
    "ERR_INTERNAL": "Wystapil nieoczekiwany blad aplikacji.",
}


def _require_form_field(name: str) -> str:
    value = (request.form.get(name) or "").strip()
    if not value:
        raise InvalidQuotationRequestError(f"Missing required form field: {name}")
    return value


def _parse_limit(default: int = 300, minimum: int = 1, maximum: int = 1000) -> int:
    raw_value = request.args.get("limit", str(default))
    try:
        return max(minimum, min(int(raw_value), maximum))
    except ValueError:
        return default


def _add_deprecation_headers(response):
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</quotations>; rel="successor-version"'
    return response


def _json_response(payload: dict, status: int):
    response = jsonify(payload)
    response.status_code = status
    return response


def _wants_json_error() -> bool:
    if request.path.startswith("/quotations"):
        return True
    if request.path.startswith("/health"):
        return True
    accepts_json = "application/json" in (request.headers.get("Accept") or "")
    xhr = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    return accepts_json or xhr


def _should_expose_error_details(error: AppError) -> bool:
    if app.debug:
        return True
    # Keep user-facing details only for validation/config-like errors.
    return error.code in {
        "ERR_INVALID_QUOTATION_REQUEST",
        "ERR_CONFIG",
        "ERR_UPLOAD_TOO_LARGE",
        "ERR_NOT_FOUND",
    }


def _validate_uploaded_excel_columns(file_content: bytes) -> None:
    try:
        data_frame = pd.read_excel(io.BytesIO(file_content), nrows=0)
    except Exception as exc:
        raise InvalidQuotationRequestError(
            "Uploaded file is not a valid Excel file."
        ) from exc

    normalized_columns = {str(column).strip() for column in data_frame.columns}
    missing_columns = [column for column in _REQUIRED_INPUT_COLUMNS if column not in normalized_columns]
    if missing_columns:
        available_columns = ", ".join(sorted(normalized_columns)) if normalized_columns else "<none>"
        raise InvalidQuotationRequestError(
            "Missing required columns: "
            f"{', '.join(missing_columns)}. "
            f"Available columns: {available_columns}"
        )


def _map_legacy_exception(error: Exception) -> AppError | None:
    if isinstance(error, AppError):
        return error
    if isinstance(error, InvalidQuotationRequestError):
        return InvalidQuotationRequestError(str(error))
    if isinstance(error, MissingEnvVarError):
        return ConfigAppError(str(error), code="ERR_CONFIG")
    if isinstance(error, DatabaseStorageError):
        return StorageAppError(str(error), code="ERR_STORAGE")
    if isinstance(error, FileNotFoundError):
        return NotFoundAppError(str(error), code="ERR_NOT_FOUND")
    if isinstance(error, SeleniumTimeoutException):
        return ExternalTimeoutAppError(str(error), code="ERR_EXTERNAL_TIMEOUT")
    if isinstance(error, (StaleElementReferenceException, WebDriverException)):
        return ExternalServiceAppError(str(error), code="ERR_EXTERNAL_SERVICE", retryable=True)
    if isinstance(error, RequestEntityTooLarge):
        return UploadTooLargeAppError(str(error))
    if isinstance(error, HTTPException):
        code = f"ERR_HTTP_{error.code}" if error.code else "ERR_HTTP"
        return AppError(error.description or str(error), code=code, status_code=error.code or 500)
    return None


def _health_checks() -> dict:
    checks = {
        "input_dir_exists": _LOCAL_INPUT_DIR.exists(),
        "output_dir_exists": _LOCAL_OUTPUT_DIR.exists(),
    }
    missing_env = [name for name in _REQUIRED_ENV_KEYS if not os.getenv(name)]
    checks["missing_env_vars"] = missing_env
    ok = checks["input_dir_exists"] and checks["output_dir_exists"] and not missing_env
    return {"status": "ok" if ok else "degraded", "checks": checks}


def _deep_health_checks() -> dict:
    result = _health_checks()
    db_available = False
    dsn = os.getenv("POSTGRES_DSN")
    if dsn:
        try:
            engine = create_engine(dsn, future=True, pool_pre_ping=True)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_available = True
        except Exception:
            db_available = False

    claas_candidates = [Path("static") / "2025_CLAAS.xlsx", Path("static") / "Claas_Prices_List.xlsx"]
    claas_price_list_path = next((path for path in claas_candidates if path.exists()), claas_candidates[0])
    result["checks"]["db_available"] = db_available
    result["checks"]["claas_price_list_exists"] = claas_price_list_path.exists()
    if not result["checks"]["claas_price_list_exists"]:
        result["status"] = "degraded"
    return result


@app.before_request
def _attach_request_id():
    g.request_id = str(uuid.uuid4())


@app.after_request
def _add_request_id_header(response):
    request_id = getattr(g, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


@app.errorhandler(AppError)
def _handle_app_error(error: AppError):
    request_id = getattr(g, "request_id", None)
    user_message = _ERROR_USER_MESSAGES.get(error.code, str(error))
    details = str(error) if _should_expose_error_details(error) else None
    payload = {
        "error": {
            "code": error.code,
            "message": user_message,
            "details": details,
            "retryable": error.retryable,
        },
        "request_id": request_id,
    }
    if _wants_json_error():
        return _json_response(payload, error.status_code)
    return (
        render_template(
            "error.html",
            message=user_message,
            details=details,
            error_code=error.code,
            request_id=request_id,
        ),
        error.status_code,
    )


@app.errorhandler(Exception)
def _handle_exception(error: Exception):
    mapped = _map_legacy_exception(error)
    if mapped is not None:
        return _handle_app_error(mapped)
    internal = AppError(str(error), code="ERR_INTERNAL", status_code=500, retryable=False)
    return _handle_app_error(internal)


# HOME PAGE
@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


# PAGE WITH MODAL FOR MARKUP, DISCOUNT, AND QUOTATION TYPE
@app.route('/chosen_brand/<ch_brand>')
def chosen_brand(ch_brand):
    client_name = request.args.get("client_name", "")
    return render_template('details.html', brand=ch_brand, client_name=client_name)


# COLLECT FORM DATA
@app.route('/details/upload/<brand>', methods=['POST'])
def details_upload(brand):
    client_name = (request.form.get("client_name") or "").strip()
    markup = _require_form_field("markup")
    discount = _require_form_field("discount")
    euro = _require_form_field("euro")
    for_client_checkbox = request.form.getlist('forClient')
    for_client = bool(for_client_checkbox)
    return render_template(
        'quotation.html',
        brand=brand,
        markup=markup,
        discount=discount,
        euro=euro,
        for_client=for_client,
        client_name=client_name,
    )


# SAVE FILE AND RUN QUOTATION FLOW
@app.route('/upload', methods=['POST'])
def upload():
    brand = _require_form_field("brand")
    markup = _require_form_field("markup")
    discount = _require_form_field("discount")
    euro = _require_form_field("euro")
    for_client = _require_form_field("for_client")
    file = request.files.get('file')
    if file is None:
        raise InvalidQuotationRequestError("Missing uploaded file.")
    filename = secure_filename(file.filename)
    if not filename:
        raise InvalidQuotationRequestError("Uploaded file has empty filename.")
    file_content = file.read()
    if not file_content:
        raise InvalidQuotationRequestError("Uploaded file is empty.")
    _validate_uploaded_excel_columns(file_content)

    stored = store_file_if_configured(
        kind="input",
        filename=filename,
        content=file_content,
        mime_type=file.mimetype or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        source_brand=brand,
    )
    if not stored:
        _LOCAL_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        (_LOCAL_INPUT_DIR / filename).write_bytes(file_content)

    quotation_request = QuotationRequest.from_raw(
        filename=filename,
        brand=brand,
        markup=markup,
        discount=discount,
        euro=euro,
        for_client=for_client,
        client_name=request.form.get("client_name", ""),
    )

    quotation_file = _DISPATCHER.execute_quotation(quotation_request)
    run_id = get_latest_run_id_by_output_filename_if_configured(quotation_file) if stored else None
    warning_message = None
    if run_id is None:
        warning_message = (
            "Wycena zostala zapisana lokalnie. Baza danych jest niedostepna, "
            "dlatego uzywany jest fallback do pliku."
        )

    return render_template(
        'summary.html',
        brand=brand,
        client_name=quotation_request.client_name,
        markup=markup,
        discount=discount,
        euro=euro,
        filename=quotation_file,
        run_id=run_id,
        warning_message=warning_message,
    )


@app.route('/local_output/<filename>/download', methods=['GET'])
def local_output_download(filename: str):
    safe_name = secure_filename(filename)
    file_path = _LOCAL_OUTPUT_DIR / safe_name
    if not file_path.exists():
        raise NotFoundAppError(f"Output file not found: {safe_name}", code="ERR_NOT_FOUND")
    return send_file(
        file_path,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=safe_name,
    )


@app.route('/uploaded_file/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
    _ = filename
    abort(
        410,
        description="Legacy endpoint removed. Use /quotations/<run_id>/download.",
    )


@app.route('/stored_files', methods=['GET'])
def stored_files():
    """Deprecated: legacy file mirror endpoint."""
    limit = _parse_limit(default=300)
    kind = request.args.get("kind") or None
    source_brand = request.args.get("brand") or None
    filename_contains = request.args.get("filename") or None

    files = list_files_filtered_if_configured(
        limit=limit,
        kind=kind,
        source_brand=source_brand,
        filename_contains=filename_contains,
    )
    return _add_deprecation_headers(jsonify(files))


@app.route('/dashboard', methods=['GET'])
def dashboard():
    return render_template('dashboard.html')


@app.route('/stored_files/<int:file_id>/download', methods=['GET'])
def stored_file_download(file_id: int):
    """Download a file payload from PostgreSQL by id."""
    record = get_file_if_configured(file_id)
    if not record:
        abort(404, description="Stored file not found.")

    response = send_file(
        io.BytesIO(record["content"]),
        mimetype=record.get("mime_type") or "application/octet-stream",
        as_attachment=True,
        download_name=record.get("filename") or f"file_{file_id}",
    )
    return _add_deprecation_headers(response)


@app.route('/stored_files/latest_output/<filename>/download', methods=['GET'])
def stored_latest_output_download(filename: str):
    _ = filename
    response = jsonify(
        {
            "error": "Legacy output mirror disabled.",
            "successor": "/quotations/<run_id>/download",
        }
    )
    response.status_code = 410
    return _add_deprecation_headers(response)


@app.route('/quotations', methods=['GET'])
def quotations():
    """List quotation runs."""
    limit = _parse_limit(default=300)
    brand = request.args.get("brand") or None
    status = request.args.get("status") or None
    runs = list_runs_if_configured(limit=limit, brand=brand, status=status)
    return jsonify(runs)


@app.route('/quotations/<int:run_id>', methods=['GET'])
def quotation_run_details(run_id: int):
    """Get quotation run details and all lines."""
    run_meta = get_run_meta_if_configured(run_id)
    if not run_meta:
        abort(404, description="Quotation run not found.")
    run_with_lines = get_run_with_lines_if_configured(run_id)
    lines = run_with_lines.get("lines", []) if run_with_lines else []
    run_meta["lines"] = lines
    return jsonify(run_meta)


@app.route('/quotations/<int:run_id>/download', methods=['GET'])
def quotation_run_download(run_id: int):
    """Generate xlsx on demand from quotation lines stored in PostgreSQL."""
    run = get_run_with_lines_if_configured(run_id)
    if not run:
        abort(404, description="Quotation run not found.")

    rows = [line["payload"] for line in run["lines"]]
    if not rows:
        abort(404, description="Quotation lines not found.")
    df = pd.DataFrame(rows)

    output_stream = io.BytesIO()
    df.to_excel(output_stream, index=False)
    output_stream.seek(0)
    output_filename = run.get("output_filename") or f"quotation_{run_id}.xlsx"
    return send_file(
        output_stream,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=output_filename,
    )


@app.route("/health", methods=["GET"])
def health():
    result = _health_checks()
    status = 200 if result["status"] == "ok" else 503
    return _json_response(result, status)


@app.route("/health/deep", methods=["GET"])
def health_deep():
    result = _deep_health_checks()
    status = 200 if result["status"] == "ok" else 503
    return _json_response(result, status)


if __name__ == '__main__':
    app.run(
        port=4999,
        debug=os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"},
    )
