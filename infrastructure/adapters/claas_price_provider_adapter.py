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
            month_price = pricelist.loc[pricelist["Part"] == float(code), "Monthly"]
            week_price = pricelist.loc[pricelist["Part"] == float(code), "Weekly"]

            if request.for_client and month_price.values.size > 0 and week_price.values.size > 0:
                client_month_price = price_for_client(
                    float(month_price.values[0]),
                    request.discount,
                    request.markup,
                    request.euro,
                )
                client_weekly_price = price_for_client(
                    float(week_price.values[0]),
                    request.discount,
                    request.markup,
                    request.euro,
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

