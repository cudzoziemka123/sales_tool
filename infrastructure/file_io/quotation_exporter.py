"""
Excel quotation exporter used by use cases.
"""

from pathlib import Path
from typing import Any, Dict

import pandas as pd


def _remove_empty_keys(quotation_data: Dict[str, Any]) -> Dict[str, Any]:
    reduced_data = quotation_data.copy()
    for key, value in quotation_data.items():
        if not value:
            del reduced_data[key]
    return reduced_data


def export_quotation(data: Dict[str, Any], document: str, output_dir: str = "for_client") -> str:
    reduced_data = _remove_empty_keys(data)
    output_filename = f"{document}_quotation.xlsx"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    if reduced_data:
        pd.DataFrame(reduced_data).to_excel(output_path / output_filename, index=False)
    else:
        pd.DataFrame().to_excel(output_path / output_filename, index=False)
    return output_filename


def export_quotation_from_lists(
    codes_list: list,
    qty_list: list,
    price_list: list,
    client_prices: list | None,
    document: str,
    output_dir: str = "for_client",
) -> str:
    output_filename = f"{document}_quotation.xlsx"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    data = {
        "Code": list(codes_list),
        "Quantity": list(qty_list),
        "Price": list(price_list),
    }
    if client_prices is not None:
        data["ClientPrice"] = list(client_prices)

    pd.DataFrame(data).to_excel(output_path / output_filename, index=False)
    return output_filename

