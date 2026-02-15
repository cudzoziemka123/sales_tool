import pandas as pd

from domain import services as domain_services


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
    """Adapter – deleguje do warstwy infrastruktury (zachowana kompatybilność wsteczna)."""
    from infrastructure.selenium.webdriver_factory import create_chrome_driver
    return create_chrome_driver()


def prepare_data(document, brand):
    """
    Adapter infrastruktury → domena.

    Tutaj wczytujemy Excela (I/O), a faktyczną logikę przygotowania
    struktur danych przekazujemy do `domain.services`.
    """
    data_dict = load_data_from_excel(document)
    return domain_services.prepare_data_from_records(data_dict, brand)


def create_quotation_file(data, document):
    """Adapter – deleguje zapis do warstwy infrastruktury."""
    from infrastructure.file_io.quotation_exporter import export_quotation
    return export_quotation(data, document)


def price_for_client(price, discount, markup, euro):
    """
    Zachowujemy to samo API, ale delegujemy logikę do warstwy domeny.
    """
    return domain_services.price_for_client(price, discount, markup, euro)
