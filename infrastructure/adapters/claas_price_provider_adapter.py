import pandas as pd

from application.dto.quotation_request import QuotationRequest
from domain.services import price_for_client


class ClaasPriceProviderAdapter:
    """Adapter reading Claas pricelist and filling quotation prices."""

    def __init__(self, pricelist_path: str = "static/2025_CLAAS.xlsx"):
        self._pricelist_path = pricelist_path
        self._pricelist: pd.DataFrame | None = None

    def _get_pricelist(self) -> pd.DataFrame:
        if self._pricelist is None:
            self._pricelist = pd.read_excel(self._pricelist_path)
        return self._pricelist

    def fill_prices(self, data: dict, request: QuotationRequest) -> None:
        pricelist = self._get_pricelist()
        for code in data["codes"]:
            try:
                code_value = float(code)
            except (TypeError, ValueError):
                data["monthly_prices"].append(0)
                data["weekly_prices"].append(0)
                if request.for_client:
                    data["prices_for_client_monthly"].append(0)
                    data["prices_for_client_weekly"].append(0)
                continue

            month_price = pricelist.loc[pricelist["Part"] == code_value, "Monthly"]
            week_price = pricelist.loc[pricelist["Part"] == code_value, "Weekly"]

            if month_price.values.size > 0 and week_price.values.size > 0:
                monthly_value = month_price.values[0]
                weekly_value = week_price.values[0]
            else:
                monthly_value = 0
                weekly_value = 0

            data["monthly_prices"].append(monthly_value)
            data["weekly_prices"].append(weekly_value)

            if request.for_client:
                client_month_price = price_for_client(
                    float(monthly_value),
                    request.discount,
                    request.markup,
                    request.euro,
                )
                client_weekly_price = price_for_client(
                    float(weekly_value),
                    request.discount,
                    request.markup,
                    request.euro,
                )
                data["prices_for_client_monthly"].append(client_month_price)
                data["prices_for_client_weekly"].append(client_weekly_price)

