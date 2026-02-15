from time import sleep

from infrastructure.config.env_loader import get_required_env
from infrastructure.scrapers.kv_scraper import (
    get_codes_list,
    get_price_list,
    get_qty_list,
    get_titles_list,
    login_kv,
    reduce_codes_by_titles,
    search_codes,
)
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class KvPriceProviderAdapter:
    """Adapter fetching quotation rows from KV ATP portal."""

    def __init__(self, base_url: str = "https://www.kvgportal.com/AtpCheck/"):
        self._base_url = base_url

    def fetch(self, search_payload: str) -> tuple[list, list, list]:
        email = get_required_env("KV_LOGIN")
        password = get_required_env("KV_PASSWORD")

        driver = create_chrome_driver()
        try:
            driver.get(self._base_url)
            sleep(3)
            login_kv(driver, email, password)
            search_codes(driver, search_payload)

            codes_list = get_codes_list(driver)
            titles_list = get_titles_list(driver)
            reduced_codes = reduce_codes_by_titles(titles_list, codes_list)
            qty_list = get_qty_list(driver)
            price_list = get_price_list(driver)
            return reduced_codes, qty_list, price_list
        finally:
            driver.quit()
