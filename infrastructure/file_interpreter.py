import io
from pathlib import Path

import pandas as pd

from domain import services as domain_services
from infrastructure.db.postgres_file_store import get_latest_file_by_name_if_configured

# TODO dodać rozdzielanie Code jesli jest spacja to wziac pierwsza czesc przed spacją.
def load_data_from_excel(document_name: str) -> list[dict]:
    record = get_latest_file_by_name_if_configured("input", document_name)
    if record and record.get("content"):
        data_file = pd.read_excel(io.BytesIO(record["content"]))
        return data_file.to_dict("records")

    local_input_path = Path("from_client") / document_name
    if not local_input_path.exists():
        raise FileNotFoundError(
            f"Input file '{document_name}' not found in PostgreSQL nor in {local_input_path.parent}."
        )
    data_file = pd.read_excel(local_input_path)
    return data_file.to_dict("records")


def prepare_data_kv(document_name: str) -> str:
    data_dict = load_data_from_excel(document_name)
    lines: list[str] = []
    for row in data_dict:
        code_raw = row.get("Code")
        qty_raw = row.get("Qty")
        if code_raw is None:
            continue

        code = str(code_raw).strip()
        if not code or code.lower() == "nan":
            continue

        qty = str(qty_raw).strip() if qty_raw is not None else "1"
        if not qty or qty.lower() == "nan":
            qty = "1"

        lines.append(f"{code} {qty}")

    data_with_wrong_letters = "\n".join(lines)
    return replace_wrong_letters(data_with_wrong_letters)


def replace_wrong_letters(data_with_wrong_letters: str) -> str:
    return data_with_wrong_letters.replace("К", "K")


def prepare_data(document: str, brand: str) -> dict:
    data_dict = load_data_from_excel(document)
    return domain_services.prepare_data_from_records(data_dict, brand)

