"""
Use case: wycena dla marki Krone.
"""

import os
from time import sleep

from env import set_env_var
from file_interpeter import prepare_data
from infrastructure.file_io.quotation_exporter import export_quotation
from infrastructure.scrapers.krone_scraper import accept_cookies_modal, login_krone, scrape_prices
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class CreateKroneQuotation:
    """Use case tworzenia wyceny Krone."""

    def __init__(self, base_url: str = "https://dealershop.agroparts.com/ads/ads-client/search/krone/igl-agrartechnik"):
        self.base_url = base_url

    def execute(self, filename: str, details: dict) -> str:
        """Wykonuje wycenę Krone."""
        set_env_var()
        login = os.environ.get("KRONE_LOGIN")
        password = os.environ.get("KRONE_PASSWORD")

        data = prepare_data(filename, details["brand"])
        driver = create_chrome_driver()
        driver.get(self.base_url)
        sleep(2)

        accept_cookies_modal(driver)
        login_krone(driver, login, password)
        scrape_prices(driver, data)

        driver.quit()
        return export_quotation(data, filename.replace(".xlsx", "") if filename.endswith(".xlsx") else filename)
