"""
Scraper cen z portalu Krone (dealershop.agroparts.com).
"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


def accept_cookies_modal(driver) -> None:
    """Obsługa modala z cookies."""
    modal = driver.switch_to.active_element
    for _ in range(4):
        modal.send_keys(Keys.TAB)
    modal.send_keys(Keys.ENTER)


def login_krone(driver, login: str, password: str) -> None:
    """Logowanie na portal Krone."""
    driver.find_element(By.ID, "aiLoginBtn").click()
    login_field = driver.find_element(By.ID, "username")
    login_field.click()
    login_field.send_keys(login)

    password_field = driver.find_element(By.ID, "password")
    password_field.click()
    password_field.send_keys(password)

    driver.find_element(By.CSS_SELECTOR, "button.button").click()
    sleep(3)


def scrape_prices(driver, data: dict) -> None:
    """Wyszukuje ceny dla kodów z data['codes'] i uzupełnia data['prices']."""
    for code in data["codes"]:
        search_field = driver.find_element(By.CLASS_NAME, value="ai-search-input")
        search_field.clear()
        search_field.click()
        search_field.send_keys(code, Keys.ENTER)
        sleep(3)
        try:
            price_field = driver.find_element(By.CLASS_NAME, value="ai-price-value")
            if price_field.text == "Price on request":
                tile = driver.find_element(By.CLASS_NAME, value="ai-product-tile")
                tile.click()
                sleep(3)
                price_field = driver.find_element(By.CLASS_NAME, value="ai-price-value")
            data["prices"].append(price_field.text.split(" ")[0])
        except NoSuchElementException:
            data["prices"].append("Not found")
