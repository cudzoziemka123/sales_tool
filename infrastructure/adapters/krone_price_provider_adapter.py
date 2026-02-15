from time import sleep

from infrastructure.config.env_loader import get_required_env
from infrastructure.scrapers.krone_scraper import accept_cookies_modal, login_krone, scrape_prices
from infrastructure.selenium.webdriver_factory import create_chrome_driver


class KronePriceProviderAdapter:
    """Adapter fetching prices from Krone portal."""

    def __init__(self, base_url: str = "https://dealershop.agroparts.com/ads/ads-client/search/krone/igl-agrartechnik"):
        self._base_url = base_url

    def fill_prices(self, brand: str, data: dict) -> None:
        del brand
        login = get_required_env("KRONE_LOGIN")
        password = get_required_env("KRONE_PASSWORD")

        driver = create_chrome_driver()
        try:
            driver.get(self._base_url)
            sleep(2)
            accept_cookies_modal(driver)
            login_krone(driver, login, password)
            scrape_prices(driver, data)
        finally:
            driver.quit()
