from flask import Flask, render_template, request, send_from_directory, current_app
from werkzeug.utils import secure_filename
from claas import do_claas_quotation
from krone import do_krone_quotation
from kv import do_kv_quotation
from samasz import do_samasz_quotaion
from parts import do_another_quotation

app = Flask(__name__)
app.config['UPLOAD_FOLDER']='for_client'

# TODO Zrobić żeby było usuwanie obu plików.
# TODO Zrobić żeby przekazywało klienta dalej -> wykorzystać w nazwie
# STRONA GŁÓWNA
@app.route('/', methods=['GET', 'POST'])
def home():
    # client = request.form['client']
    return render_template('index.html')

# STRONA Z MODALEM DO WYBORU MARŻY, RABATU I RODZAJU WYCENY
@app.route('/chosen_brand/<ch_brand>')
def chosen_brand(ch_brand):
    return render_template('details.html', brand=ch_brand)


# ZBIERA DANE Z MODALU
@app.route('/details/upload/<brand>', methods=['GET', 'POST'])
def details_upload(brand):
    markup=request.form['markup']
    discount=request.form['discount']
    euro=request.form['euro']
    for_client_checkbox = request.form.getlist('forClient')
    if for_client_checkbox:
         for_client=True
    else:
        for_client=False
    return render_template('quotation.html', brand=brand, markup=markup, discount=discount, euro=euro, for_client=for_client)

# ZAPISUJE PLIK I ODPALA SKRYPT Z WYCENIANIEM
@app.route('/upload/<brand>/<markup>/<discount>/<euro>/<for_client>', methods=['GET','POST'])
def upload(brand, markup, discount, euro, for_client):
    # TODO Zrobić obróbkę błędu kiedy nie ma kolumn Code i Qty w dokumencie
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(f'from_client/{filename}')
    details={
        'brand': brand,
        'markup': markup,
        'discount': discount,
        'euro': euro,
        'for_client': for_client,
    }

    if brand == 'Samasz':
        quotation_file = do_samasz_quotaion(filename, details)
    elif brand == 'Kverneland':
        quotation_file=do_kv_quotation(filename, details)
    elif brand == 'Claas':
        quotation_file=do_claas_quotation(filename, details)
    elif brand == 'Krone':
        quotation_file=do_krone_quotation(filename, details)
    else:
        quotation_file=do_another_quotation(filename, details)

    return render_template('summary.html', brand=brand, markup=markup, discount=discount, euro=euro, filename=quotation_file)

@app.route('/uploaded_file/<filename>', methods=['GET', 'POST'])
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == '__main__':
    app.run(port=4999, debug=True)