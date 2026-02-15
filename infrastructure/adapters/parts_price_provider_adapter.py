from time import sleep

from infrastructure.config.env_loader import get_required_env
from infrastructure.scrapers.parts_scraper import login_to_account, scrape_prices
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class PartsPriceProviderAdapter:
    """Adapter fetching prices from 0parts.com."""

    def __init__(self, base_url: str = "https://0parts.com/"):
        self._base_url = base_url

    def fill_prices(self, brand: str, data: dict) -> None:
        login = get_required_env("PARTS_LOGIN")
        password = get_required_env("PARTS_PASSWORD")

        driver = create_chrome_driver()
        try:
            driver.get(self._base_url)
            sleep(2)
            login_to_account(driver, login, password)
            sleep(3)
            scrape_prices(driver, brand, data)
            sleep(3)
        finally:
            driver.quit()
