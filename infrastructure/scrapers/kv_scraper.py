"""
Scraper cen z portalu Kverneland (kvgportal.com/AtpCheck).
"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def login_kv(driver, email: str, password: str) -> None:
    """Logowanie na portal Kverneland."""
    btn = driver.find_element(By.CLASS_NAME, value="btn-primary")
    btn.click()
    sleep(5)

    email_field = driver.find_element(By.NAME, value="Email Address")
    email_field.click()
    email_field.send_keys(email)

    password_field = driver.find_element(By.NAME, value="Password")
    password_field.click()
    password_field.send_keys(password)

    login_btn = driver.find_element(By.ID, value="next")
    login_btn.click()
    sleep(8)


def search_codes(driver, data: str) -> None:
    """Wyszukuje kody na stronie ATP Check."""
    search_field = driver.find_element(By.CLASS_NAME, value="searchBar")
    search_field.click()
    search_field.send_keys(data, Keys.ENTER)
    sleep(2)
    driver.find_element(By.CLASS_NAME, value="submitButton").click()
    sleep(60)


def get_codes_list(driver) -> list:
    """Pobiera listę kodów ze strony."""
    codes_web_list = driver.find_elements(By.CLASS_NAME, value="warehouseName")
    return [code.text for code in codes_web_list]


def get_titles_list(driver) -> list:
    """Pobiera listę tytułów (walidacja: NOT FOUND / nazwa produktu)."""
    is_it_valid_web_list = driver.find_elements(By.CLASS_NAME, value="card-title")
    return [title.text for title in is_it_valid_web_list]


def get_qty_list(driver) -> list:
    """Pobiera listę ilości ze strony."""
    qty_web_list = driver.find_elements(By.ID, value="atpQuantity")
    return [qty.text for qty in qty_web_list]


def get_price_list(driver) -> list:
    """Pobiera listę cen (PLN) ze strony."""
    details_list = driver.find_elements(By.CSS_SELECTOR, value="td.materialCardResult div")
    prices = []
    for detail in details_list:
        if "PLN" in detail.text:
            price_without_currency = detail.text.split(" ")[0]
            price_without_dots = price_without_currency.replace(".", "")
            prices.append(price_without_dots)
    return prices


def reduce_codes_by_titles(titles_list: list, codes_list: list) -> list:
    """Usuwa kody odpowiadające pozycjom 'NOT FOUND' w titles_list."""
    result = codes_list.copy()
    index = 0
    for title in titles_list:
        if title == "NOT FOUND":
            del result[index]
        else:
            index += 1
    return result
