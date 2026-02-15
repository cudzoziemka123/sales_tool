import io

from flask import Flask, abort, jsonify, render_template, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from application.dto.quotation_request import InvalidQuotationRequestError, QuotationRequest
from infrastructure.config.env_loader import MissingEnvVarError
from infrastructure.db.postgres_file_store import (
    DatabaseStorageError,
    get_file_if_configured,
    get_latest_file_by_name_if_configured,
    list_files_filtered_if_configured,
    store_file_if_configured,
)
from presentation.bootstrap import get_dispatcher

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'for_client'
_DISPATCHER = get_dispatcher()


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
@app.route('/', methods=['GET', 'POST'])
def home():
    # client = request.form['client']
    return render_template('index.html')


# PAGE WITH MODAL FOR MARKUP, DISCOUNT, AND QUOTATION TYPE
@app.route('/chosen_brand/<ch_brand>')
def chosen_brand(ch_brand):
    return render_template('details.html', brand=ch_brand)


# COLLECT FORM DATA
@app.route('/details/upload/<brand>', methods=['GET', 'POST'])
def details_upload(brand):
    markup = request.form['markup']
    discount = request.form['discount']
    euro = request.form['euro']
    for_client_checkbox = request.form.getlist('forClient')
    for_client = bool(for_client_checkbox)
    return render_template(
        'quotation.html',
        brand=brand,
        markup=markup,
        discount=discount,
        euro=euro,
        for_client=for_client,
    )


# SAVE FILE AND RUN QUOTATION FLOW
@app.route('/upload/<brand>/<markup>/<discount>/<euro>/<for_client>', methods=['GET', 'POST'])
def upload(brand, markup, discount, euro, for_client):
    # TODO add error handling for missing Code/Qty columns
    file = request.files['file']
    filename = secure_filename(file.filename)
    file_content = file.read()

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
    )

    quotation_file = _DISPATCHER.execute_quotation(quotation_request)
    return render_template(
        'summary.html',
        brand=brand,
        markup=markup,
        discount=discount,
        euro=euro,
        filename=quotation_file,
    )


@app.route('/uploaded_file/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/stored_files', methods=['GET'])
def stored_files():
    """List recent files mirrored to PostgreSQL, optionally filtered."""
    limit_raw = request.args.get("limit", "300")
    try:
        limit = max(1, min(int(limit_raw), 1000))
    except ValueError:
        limit = 300
    kind = request.args.get("kind") or None
    source_brand = request.args.get("brand") or None
    filename_contains = request.args.get("filename") or None

    files = list_files_filtered_if_configured(
        limit=limit,
        kind=kind,
        source_brand=source_brand,
        filename_contains=filename_contains,
    )
    return jsonify(files)


@app.route('/stored_files/<int:file_id>/download', methods=['GET'])
def stored_file_download(file_id: int):
    """Download a file payload from PostgreSQL by id."""
    record = get_file_if_configured(file_id)
    if not record:
        abort(404, description="Stored file not found.")

    return send_file(
        io.BytesIO(record["content"]),
        mimetype=record.get("mime_type") or "application/octet-stream",
        as_attachment=True,
        download_name=record.get("filename") or f"file_{file_id}",
    )


@app.route('/stored_files/latest_output/<filename>/download', methods=['GET'])
def stored_latest_output_download(filename: str):
    """Download latest generated output file by filename."""
    record = get_latest_file_by_name_if_configured("output", filename)
    if not record:
        abort(404, description="Stored output file not found.")

    return send_file(
        io.BytesIO(record["content"]),
        mimetype=record.get("mime_type") or "application/octet-stream",
        as_attachment=True,
        download_name=record.get("filename") or filename,
    )


if __name__ == '__main__':
    app.run(port=4999, debug=True)
