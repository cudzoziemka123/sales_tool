"""
Use case: wycena dla marek z portalu 0parts.com.
"""

import os
from time import sleep

from env import set_env_var
from file_interpeter import prepare_data
from infrastructure.file_io.quotation_exporter import export_quotation
from infrastructure.scrapers.parts_scraper import login_to_account, scrape_prices
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class CreatePartsQuotation:
    """Use case tworzenia wyceny dla marek (0parts.com)."""

    def __init__(self, base_url: str = "https://0parts.com/"):
        self.base_url = base_url

    def execute(self, filename: str, details: dict) -> str:
        """Wykonuje wycenę – logowanie, wyszukanie cen, eksport."""
        set_env_var()
        login = os.getenv("PARTS_LOGIN")
        password = os.getenv("PARTS_PASSWORD")

        data = prepare_data(filename, details["brand"])
        driver = create_chrome_driver()
        driver.get(self.base_url)
        sleep(2)

        login_to_account(driver, login, password)
        sleep(3)
        scrape_prices(driver, details["brand"], data)

        driver.quit()
        sleep(3)

        return export_quotation(data, filename)
