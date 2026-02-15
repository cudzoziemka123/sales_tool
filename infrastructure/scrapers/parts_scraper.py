"""
Scraper cen z portalu 0parts.com.
"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


def login_to_account(driver, login: str, password: str) -> None:
    """Logowanie na portal 0parts.com."""
    login_link = driver.find_element(By.CLASS_NAME, value="loginLink")
    login_link.click()

    login_field = driver.find_element(By.ID, value="login_modal")
    login_field.click()
    login_field.send_keys(login)

    password_field = driver.find_element(By.ID, value="pass_modal")
    password_field.click()
    password_field.send_keys(password)

    login_btn = driver.find_element(By.ID, value="go_modal")
    login_btn.click()
    sleep(3)


def _find_price(driver, code: str) -> None:
    """Wyszukuje kod w polu wyszukiwania."""
    search_field = driver.find_element(By.ID, value="pcode")
    search_field.click()
    search_field.clear()
    search_field.send_keys(code, Keys.ENTER)


def _get_price_by_code(driver, data: dict) -> None:
    """Pobiera cenę z bestOfferPrice i dodaje do data['prices']."""
    price = driver.find_element(By.CLASS_NAME, value="bestOfferPrice")
    data["prices"].append(price.text.split(" ")[0].replace("€", ""))


def _get_price_by_brand(driver, brand: str, data: dict) -> None:
    """Próba pobrania ceny po marce (jeśli nie znaleziono po kodzie)."""
    case_brands = driver.find_elements(By.CLASS_NAME, value="caseBrand")
    case_code = driver.find_element(By.CLASS_NAME, value="casePartCode")
    for case_brand in case_brands:
        if case_brand.text.lower() == brand.lower():
            case_code.click()
            sleep(3)
            _get_price_by_code(driver, data)
            return
    data["prices"].append("Brak ceny")


def scrape_prices(driver, brand: str, data: dict) -> None:
    """Wyszukuje ceny dla kodów z data['codes'] i uzupełnia data['prices']."""
    for code in data["codes"]:
        _find_price(driver, code)
        sleep(3)
        try:
            _get_price_by_code(driver, data)
        except NoSuchElementException:
            try:
                _get_price_by_brand(driver, brand, data)
            except NoSuchElementException:
                data["prices"].append("Brak ceny")
        sleep(3)
