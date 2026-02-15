"""
Use case: wycena dla marki Claas.

Orkiestruje przepływ: przygotowanie danych → wyszukanie cen w cenniku → obliczenie cen dla klienta → eksport do Excel.
"""

import pandas as pd

from domain.services import price_for_client
from infrastructure.file_io.quotation_exporter import export_quotation


class CreateClaasQuotation:
    """Use case tworzenia wyceny Claas."""

    def __init__(self, pricelist_path: str = "static/2025_CLAAS.xlsx"):
        self.pricelist_path = pricelist_path
        self._pricelist: pd.DataFrame | None = None

    def _get_pricelist(self) -> pd.DataFrame:
        if self._pricelist is None:
            self._pricelist = pd.read_excel(self.pricelist_path)
        return self._pricelist

    def execute(self, filename: str, details: dict) -> str:
        """
        Wykonuje wycenę Claas.

        Args:
            filename: nazwa przesłanego pliku z pozycjami
            details: słownik z brand, for_client, discount, markup, euro

        Returns:
            Nazwa wygenerowanego pliku wyceny
        """
        from file_interpeter import prepare_data

        data = prepare_data(filename, details["brand"])
        pricelist = self._get_pricelist()

        for code in data["codes"]:
            month_price = pricelist.loc[pricelist["Part"] == float(code), "Monthly"]
            week_price = pricelist.loc[pricelist["Part"] == float(code), "Weekly"]

            if str(details.get("for_client", False)).lower() == "true":
                client_month_price = price_for_client(
                    float(month_price.values[0]),
                    float(details["discount"]),
                    float(details["markup"]),
                    float(details["euro"]),
                )
                client_weekly_price = price_for_client(
                    float(week_price.values[0]),
                    float(details["discount"]),
                    float(details["markup"]),
                    float(details["euro"]),
                )
                data["prices_for_client_monthly"].append(client_month_price)
                data["prices_for_client_weekly"].append(client_weekly_price)
            else:
                if month_price.values.size > 0 and week_price.values.size > 0:
                    data["monthly_prices"].append(month_price.values[0])
                    data["weekly_prices"].append(week_price.values[0])
                else:
                    data["monthly_prices"].append(0)
                    data["weekly_prices"].append(0)

        return export_quotation(data, filename)
