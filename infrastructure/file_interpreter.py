import pandas as pd

from domain import services as domain_services


def load_data_from_excel(document_name: str) -> list[dict]:
    data_file = pd.read_excel(f"from_client/{document_name}")
    return data_file.to_dict("records")


def prepare_data_kv(document_name: str) -> str:
    data_dict = load_data_from_excel(document_name)
    data_list = [f"{data_el['Code']} {data_el['Qty']}" for data_el in data_dict]
    data_with_wrong_letters = " ".join(data_list)
    return replace_wrong_letters(data_with_wrong_letters)


def replace_wrong_letters(data_with_wrong_letters: str) -> str:
    return data_with_wrong_letters.replace("Đš", "K")


def prepare_data(document: str, brand: str) -> dict:
    data_dict = load_data_from_excel(document)
    return domain_services.prepare_data_from_records(data_dict, brand)

