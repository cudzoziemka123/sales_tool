import importlib.util
import unittest

SELENIUM_AVAILABLE = importlib.util.find_spec("selenium") is not None


@unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium is not installed in current environment.")
class SamaszPriceParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from infrastructure.scrapers.samasz_scraper import _extract_price_value

        cls._extract_price_value = staticmethod(_extract_price_value)

    def test_extract_price_with_space_separator(self):
        self.assertEqual(self._extract_price_value("1 500 PLN"), "1500")

    def test_extract_price_with_decimal_part(self):
        self.assertEqual(self._extract_price_value("3 000,50 PLN"), "3000,50")

    def test_raises_on_missing_number(self):
        with self.assertRaises(ValueError):
            self._extract_price_value("Brak ceny")


if __name__ == "__main__":
    unittest.main()
