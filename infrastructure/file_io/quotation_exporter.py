"""
Eksport wycen do plików Excel.

Warstwa infrastruktury – odpowiedzialna za I/O (zapis do pliku).
"""

import pandas as pd
from typing import Any, Dict

from infrastructure.db.postgres_file_store import store_file_if_configured

def _remove_empty_keys(quotation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Usuwa klucze ze słownika, których wartości są puste."""
    reduced_data = quotation_data.copy()
    for key, value in quotation_data.items():
        if not value:
            del reduced_data[key]
    return reduced_data


def export_quotation(data: Dict[str, Any], document: str, output_dir: str = "for_client") -> str:
    """
    Zapisuje wycenę do pliku Excel.

    Args:
        data: słownik z kluczami np. codes, qty, monthly_prices, prices_for_client_monthly
        document: nazwa dokumentu (bez rozszerzenia) – do budowy nazwy pliku
        output_dir: katalog docelowy (domyślnie for_client)

    Returns:
        Nazwa wygenerowanego pliku (np. "dokument_quotation.xlsx")
    """
    reduced_data = _remove_empty_keys(data)
    quotation = pd.DataFrame(reduced_data)
    filename = f"{document}_quotation.xlsx"
    output_path = f"{output_dir}/{filename}"
    quotation.to_excel(output_path, index=False)
    with open(output_path, "rb") as generated_file:
        store_file_if_configured(
            kind="output",
            filename=filename,
            content=generated_file.read(),
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    return filename


def export_quotation_from_lists(
    codes_list: list,
    qty_list: list,
    price_list: list,
    document: str,
    output_dir: str = "for_client",
) -> str:
    """
    Zapisuje wycenę do pliku Excel (format KV – kolumny Code, Quantity, Price).

    Args:
        codes_list: lista kodów części
        qty_list: lista ilości
        price_list: lista cen
        document: nazwa dokumentu (bez rozszerzenia)
        output_dir: katalog docelowy

    Returns:
        Nazwa wygenerowanego pliku (np. "dokument_quotation.xlsx")
    """
    quotation = pd.DataFrame(
        {"Code": codes_list, "Quantity": qty_list, "Price": price_list}
    )
    filename = f"{document}_quotation.xlsx"
    output_path = f"{output_dir}/{filename}"
    quotation.to_excel(output_path, index=False)
    with open(output_path, "rb") as generated_file:
        store_file_if_configured(
            kind="output",
            filename=filename,
            content=generated_file.read(),
            mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    return filename
