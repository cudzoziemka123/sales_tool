"""
Use case: wycena dla marki Samasz.
"""

import os
from time import sleep

from env import set_env_var
from file_interpeter import prepare_data
from infrastructure.file_io.quotation_exporter import export_quotation
from infrastructure.scrapers.samasz_scraper import login_samasz, scrape_prices
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class CreateSamaszQuotation:
    """Use case tworzenia wyceny Samasz."""

    def __init__(self, base_url: str = "https://kontrahenci.samasz.pl/login"):
        self.base_url = base_url

    def execute(self, filename: str, details: dict) -> str:
        """
        Wykonuje wycenę Samasz – logowanie na portal, wyszukanie cen, eksport.
        """
        set_env_var()
        company = os.environ.get("SAMASZ_COMPANY")
        email = os.environ.get("SAMASZ_LOGIN")
        password = os.environ.get("SAMASZ_PASSWORD")

        data = prepare_data(filename, details["brand"])
        driver = create_chrome_driver()
        driver.get(self.base_url)
        sleep(5)

        login_samasz(driver, company, email, password)
        sleep(5)
        scrape_prices(driver, data)
        driver.quit()

        return export_quotation(data, filename)
