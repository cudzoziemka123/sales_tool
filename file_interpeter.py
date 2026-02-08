import pandas as pd
from selenium import webdriver

def load_data_from_excel(document_name):
    data_file = pd.read_excel(f"from_client/{document_name}")
    data_dict = data_file.to_dict("records")
    return data_dict

# TODO Można to przerobić żeby było w prepare_data
def prepare_data_kv(document_name):
    data_dict = load_data_from_excel(document_name)
    data_list = [f"{data_el["Code"]} {data_el["Qty"]}" for data_el in data_dict]
    data_with_wrong_letters = " ".join(data_list)
    data=replace_wrong_letters(data_with_wrong_letters)
    return data

def replace_wrong_letters(data_with_wrong_letters):
    data = data_with_wrong_letters.replace("К", "K")
    return data

def set_webdriver_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    driver_chrome = webdriver.Chrome(options=chrome_options)
    return driver_chrome

def add_zeros_for_horsch(code):
    if len(code) < 7:
        new_code = code.rjust(8 - len(code) + len(code), '0')
    else:
        new_code = code
    return new_code


def reduce_floats(el):
    code_str = str(el["Code"]).split(".")[0]
    qty_str = str(el["Qty"]).split(".")[0]
    return {'code_str': code_str, 'qty_str': qty_str}

def prepare_data(document,brand):
    data = {
        'codes': [],
        'qty': [],
        'monthly_prices': [],
        'weekly_prices': [],
        'samasz_codes': [],
        'prices': [],
    }

    data_dict = load_data_from_excel(document)
    # if brand == "Kverneland":
    #     data_kv=prepare_data_kv(data_dict)
    #     return data_kv
    #
    for data_el in data_dict:
        if brand != "Samasz":
            reduced_data_el = reduce_floats(data_el)
            qty_str = reduced_data_el['qty_str']

            if brand == "Horsch":
                code_str = add_zeros_for_horsch(reduced_data_el['code_str'])
            else:
                code_str = reduced_data_el['code_str']

        else:
            code_str = str(data_el["Code"])
            qty_str = str(data_el["Qty"])

        data['codes'].append(str(code_str))
        data['qty'].append(qty_str)
    return data


def create_quotation_file(data, document):
    # ZAPISYWANIE WYCENY DO PLIKU EXCEL
    reduced_data= remove_empty_keys(data)
    quotation = pd.DataFrame(reduced_data)
    filename=f"{document}_quotation.xlsx"
    quotation.to_excel(f"for_client/{filename}",index=False)
    return filename

def remove_empty_keys(quotation_data):
    reduced_data=quotation_data.copy()
    for key, value in quotation_data.items():
        if not value:
            del reduced_data[key]
    return reduced_data

# TODO Wycena dla klienta