import io

import pandas as pd

from domain import services as domain_services
from infrastructure.db.postgres_file_store import get_latest_file_by_name_if_configured


def load_data_from_excel(document_name: str) -> list[dict]:
    record = get_latest_file_by_name_if_configured("input", document_name)
    if not record or not record.get("content"):
        raise FileNotFoundError(f"Input file '{document_name}' not found in PostgreSQL.")
    data_file = pd.read_excel(io.BytesIO(record["content"]))
    return data_file.to_dict("records")


def prepare_data_kv(document_name: str) -> str:
    data_dict = load_data_from_excel(document_name)
    data_list = [f"{data_el['Code']} {data_el['Qty']}" for data_el in data_dict]
    data_with_wrong_letters = " ".join(data_list)
    return replace_wrong_letters(data_with_wrong_letters)


def replace_wrong_letters(data_with_wrong_letters: str) -> str:
    return data_with_wrong_letters.replace("К", "K")


def prepare_data(document: str, brand: str) -> dict:
    data_dict = load_data_from_excel(document)
    return domain_services.prepare_data_from_records(data_dict, brand)

