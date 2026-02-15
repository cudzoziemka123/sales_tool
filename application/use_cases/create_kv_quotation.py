"""
Use case: wycena dla marki Kverneland (KV).
"""

import os
from time import sleep

from env import set_env_var
from file_interpeter import prepare_data_kv
from infrastructure.file_io.quotation_exporter import export_quotation_from_lists
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


class CreateKvQuotation:
    """Use case tworzenia wyceny Kverneland."""

    def __init__(self, base_url: str = "https://www.kvgportal.com/AtpCheck/"):
        self.base_url = base_url

    def execute(self, filename: str, details: dict) -> str:
        """Wykonuje wycenę KV – ATP Check, pobranie cen, eksport."""
        set_env_var()
        email = os.getenv("KV_LOGIN")
        password = os.getenv("KV_PASSWORD")

        data = prepare_data_kv(filename)
        driver = create_chrome_driver()
        driver.get(self.base_url)
        sleep(3)

        login_kv(driver, email, password)
        search_codes(driver, data)

        codes_list = get_codes_list(driver)
        titles_list = get_titles_list(driver)
        codes_list = reduce_codes_by_titles(titles_list, codes_list)
        qty_list = get_qty_list(driver)
        price_list = get_price_list(driver)

        driver.quit()

        document = filename.replace(".xlsx", "") if filename.endswith(".xlsx") else filename
        return export_quotation_from_lists(codes_list, qty_list, price_list, document)
