"""
Legacy exporter interface.

In DB-first mode we keep filename contract for use cases, while the actual
download file is generated on-demand from quotation lines stored in PostgreSQL.
"""

from typing import Any, Dict


def _remove_empty_keys(quotation_data: Dict[str, Any]) -> Dict[str, Any]:
    reduced_data = quotation_data.copy()
    for key, value in quotation_data.items():
        if not value:
            del reduced_data[key]
    return reduced_data


def export_quotation(data: Dict[str, Any], document: str, output_dir: str = "for_client") -> str:
    _ = _remove_empty_keys(data)
    _ = output_dir
    return f"{document}_quotation.xlsx"


def export_quotation_from_lists(
    codes_list: list,
    qty_list: list,
    price_list: list,
    document: str,
    output_dir: str = "for_client",
) -> str:
    _ = (codes_list, qty_list, price_list, output_dir)
    return f"{document}_quotation.xlsx"

