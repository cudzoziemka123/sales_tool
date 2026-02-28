import unittest

from domain.services import (
    apply_client_prices_to_data,
    apply_client_prices_to_list,
    parse_price_to_float,
    price_for_client,
)


class DiscountHandlingTests(unittest.TestCase):
    def test_price_for_client_accepts_fraction_discount(self):
        result = price_for_client(price=100.0, discount=0.15, markup=10.0, euro=4.0)
        self.assertEqual(result, 23.38)

    def test_price_for_client_accepts_percent_discount(self):
        as_percent = price_for_client(price=100.0, discount=15.0, markup=10.0, euro=4.0)
        as_fraction = price_for_client(price=100.0, discount=0.15, markup=10.0, euro=4.0)
        self.assertEqual(as_percent, as_fraction)

    def test_parse_price_to_float_handles_currency_text(self):
        self.assertEqual(parse_price_to_float("1 500 PLN"), 1500.0)
        self.assertEqual(parse_price_to_float("1.250,00 PLN"), 1250.0)

    def test_apply_client_prices_to_data_keeps_non_numeric_rows(self):
        data = {"prices": ["Nie znaleziono", "1234.0"]}
        apply_client_prices_to_data(data, discount=15.0, markup=24.0, euro=4.0)
        self.assertEqual(data["prices_for_client"][0], "Nie znaleziono")
        self.assertEqual(data["prices_for_client"][1], 325.16)

    def test_apply_client_prices_to_list_keeps_non_numeric_rows(self):
        prices = ["Brak ceny", "100,00 PLN"]
        result = apply_client_prices_to_list(prices, discount=10.0, markup=20.0, euro=4.0)
        self.assertEqual(result[0], "Brak ceny")
        self.assertEqual(result[1], 27.0)


if __name__ == "__main__":
    unittest.main()
