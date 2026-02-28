from time import sleep

from infrastructure.config.env_loader import get_required_env
from infrastructure.scrapers.samasz_scraper import login_samasz, scrape_prices, warmup_samasz
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class SamaszPriceProviderAdapter:
    """Adapter fetching prices from Samasz portal."""

    def __init__(self, base_url: str = "https://kontrahenci.samasz.pl/login"):
        self._base_url = base_url

    def fill_prices(self, brand: str, data: dict) -> None:
        del brand
        company = get_required_env("SAMASZ_COMPANY")
        email = get_required_env("SAMASZ_LOGIN")
        password = get_required_env("SAMASZ_PASSWORD")

        driver = create_chrome_driver()
        try:
            driver.get(self._base_url)
            sleep(5)
            login_samasz(driver, company, email, password)
            warmup_samasz(driver)
            scrape_prices(driver, data)
        finally:
            driver.quit()
