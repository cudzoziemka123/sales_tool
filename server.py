import io

from flask import Flask, abort, jsonify, render_template, request, send_file
import pandas as pd
from werkzeug.utils import secure_filename

from application.dto.quotation_request import InvalidQuotationRequestError, QuotationRequest
from infrastructure.config.env_loader import MissingEnvVarError
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
_DISPATCHER = get_dispatcher()
_REQUIRED_INPUT_COLUMNS = ("Code", "Qty")


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


@app.errorhandler(InvalidQuotationRequestError)
def handle_invalid_quotation_request(error):
    return str(error), 400


@app.errorhandler(MissingEnvVarError)
def handle_missing_env_var(error):
    return str(error), 500


@app.errorhandler(DatabaseStorageError)
def handle_db_storage_error(error):
    return str(error), 500


@app.errorhandler(FileNotFoundError)
def handle_file_not_found(error):
    return str(error), 500


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
        raise DatabaseStorageError("Input file could not be stored in PostgreSQL.")

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
    run_id = get_latest_run_id_by_output_filename_if_configured(quotation_file)
    if run_id is None:
        raise DatabaseStorageError(
            "Quotation run was not persisted in PostgreSQL. "
            "Output file is available only from quotation runs."
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
    """List recent files mirrored to PostgreSQL, optionally filtered."""
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


if __name__ == '__main__':
    app.run(port=4999, debug=True)
