import unittest

import pandas as pd

from application.dto.quotation_request import QuotationRequest
from domain.services import price_for_client
from infrastructure.adapters.claas_price_provider_adapter import ClaasPriceProviderAdapter


class ClaasPriceProviderAdapterTests(unittest.TestCase):
    def test_fill_prices_for_client_keeps_purchase_and_client_columns_aligned(self):
        adapter = ClaasPriceProviderAdapter(pricelist_path="unused.xlsx")
        adapter._pricelist = pd.DataFrame(
            {
                "Part": [123.0],
                "Monthly": [1000.0],
                "Weekly": [400.0],
            }
        )

        request = QuotationRequest.from_raw(
            filename="doc.xlsx",
            brand="Claas",
            markup="10",
            discount="15",
            euro="4",
            for_client="true",
        )
        data = {
            "codes": ["123", "NON_NUMERIC"],
            "monthly_prices": [],
            "weekly_prices": [],
            "prices_for_client_monthly": [],
            "prices_for_client_weekly": [],
        }

        adapter.fill_prices(data, request)

        self.assertEqual(data["monthly_prices"], [1000.0, 0])
        self.assertEqual(data["weekly_prices"], [400.0, 0])
        self.assertEqual(
            data["prices_for_client_monthly"],
            [price_for_client(1000.0, 15.0, 10.0, 4.0), 0],
        )
        self.assertEqual(
            data["prices_for_client_weekly"],
            [price_for_client(400.0, 15.0, 10.0, 4.0), 0],
        )


if __name__ == "__main__":
    unittest.main()
