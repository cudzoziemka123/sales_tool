from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from application.dto.quotation_request import InvalidQuotationRequestError, QuotationRequest
from infrastructure.config.env_loader import MissingEnvVarError
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
    file.save(f'from_client/{filename}')

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


if __name__ == '__main__':
    app.run(port=4999, debug=True)
