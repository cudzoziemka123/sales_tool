"""
Scraper cen z portalu Samasz (kontrahenci.samasz.pl).
"""

from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException


def login_samasz(driver, company: str, email: str, password: str) -> None:
    """Logowanie na portal Samasz."""
    company_field = driver.find_element(By.ID, value="customerName-field")
    company_field.click()
    company_field.send_keys(company)

    employee_field = driver.find_element(By.ID, value="userName-field")
    employee_field.click()
    employee_field.send_keys(email)

    password_field = driver.find_element(By.ID, value="password-field")
    password_field.click()
    password_field.send_keys(password)
    sleep(5)

    terms_check = driver.find_elements(By.CLASS_NAME, value="ti-check")
    for check in terms_check:
        check.click()
    sleep(3)

    log_on_btn = driver.find_element(By.CLASS_NAME, value="primary-action")
    log_on_btn.click()
    sleep(5)


def scrape_prices(driver, data: dict) -> None:
    """Wyszukuje ceny dla kodów z data['codes'] i uzupełnia data['prices'], data['samasz_codes']."""
    for code in data["codes"]:
        search_field = driver.find_element(By.ID, value="searchPhrase-field")
        search_field.click()
        sleep(5)
        search_field.clear()
        search_field.send_keys(code, Keys.ENTER)
        sleep(6)
        try:
            price = driver.find_element(By.CLASS_NAME, value="basic-price")
            samasz_code = driver.find_element(By.CLASS_NAME, value="product-code")
            data["prices"].append(price.text.split(" ")[0])
            data["samasz_codes"].append(samasz_code.text)
        except NoSuchElementException:
            data["prices"].append("Nie znaleziono")
            data["samasz_codes"].append("Nie znaleziono")
