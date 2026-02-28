"""
Scraper cen z portalu Samasz (kontrahenci.samasz.pl).
"""

import re
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


def _extract_price_value(raw_price: str) -> str:
    """
    Extract numeric value from price text.

    Handles values with thousand separators, e.g.:
    - "1 500 PLN" -> "1500"
    - "3 000,50 PLN" -> "3000,50"
    """
    match = re.search(r"\d[\d\s]*(?:[.,]\d+)?", raw_price)
    if not match:
        raise ValueError(f"Cannot parse price from: {raw_price!r}")
    return match.group(0).replace(" ", "")


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


def warmup_samasz(driver) -> None:
    """
    Warm-up after login: wait until search UI is interactable.
    This reduces flaky first-queries right after session init.
    """
    _wait_for_loading(driver, timeout=20)
    field = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "searchPhrase-field"))
    )
    field.click()
    field.clear()
    _wait_for_loading(driver, timeout=10)


def _wait_for_loading(driver, timeout: int = 15) -> None:
    """Ждёт, пока overlay загрузки исчезнет со страницы."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located(
                (By.CSS_SELECTOR, "app-loading"))
        )
    except TimeoutException:
        pass  # если overlay не появился — продолжаем


def _read_result_texts(driver) -> tuple[str, str] | None:
    """
    Returns raw (price_text, product_code_text) currently visible on page.
    """
    try:
        price_el = driver.find_element(By.CLASS_NAME, value="basic-price")
        code_el = driver.find_element(By.CLASS_NAME, value="product-code")
        price_text = (price_el.text or "").strip()
        code_text = (code_el.text or "").strip()
        if not price_text or not code_text:
            return None
        return price_text, code_text
    except NoSuchElementException:
        return None


def _wait_for_result_refresh(
    driver,
    previous_result: tuple[str, str] | None,
    timeout: int = 10,
    poll_seconds: float = 0.5,
) -> tuple[str, str] | None:
    """
    Waits until search result is refreshed after submitting a new code.
    It avoids reusing stale result from previous code.
    """
    elapsed = 0.0
    while elapsed < timeout:
        _wait_for_loading(driver, timeout=3)
        current = _read_result_texts(driver)

        # No visible result yet, keep waiting.
        if current is None:
            sleep(poll_seconds)
            elapsed += poll_seconds
            continue

        # First result on page.
        if previous_result is None:
            return current

        # Result changed vs previous code; wait one more poll to ensure stability.
        if current != previous_result:
            sleep(poll_seconds)
            confirm = _read_result_texts(driver)
            return confirm if confirm is not None else current

        sleep(poll_seconds)
        elapsed += poll_seconds

    return None


def scrape_prices(driver, data: dict) -> None:
    """Wyszukuje ceny dla kodów z data['codes'] i uzupełnia data['prices'], data['samasz_codes']."""
    for code in data["codes"]:
        result = None
        # Retry once per code because Samasz UI sometimes lags behind Enter.
        for attempt in range(2):
            previous_result = _read_result_texts(driver)
            _wait_for_loading(driver, timeout=10)
            search_field = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.ID, "searchPhrase-field"))
            )
            search_field.click()
            search_field.clear()
            search_field.send_keys(code, Keys.ENTER)

            refreshed_result = _wait_for_result_refresh(
                driver,
                previous_result=previous_result,
                timeout=35 if attempt == 0 else 50,
            )
            if refreshed_result is not None:
                result = refreshed_result
                break
            sleep(2)

        if result is None:
            data["prices"].append("Nie znaleziono")
            data["samasz_codes"].append("Nie znaleziono")
            continue

        price_text, code_text = result
        try:
            parsed_price = _extract_price_value(price_text)
            data["prices"].append(parsed_price)
            data["samasz_codes"].append(code_text)
        except ValueError:
            data["prices"].append("Nie znaleziono")
            data["samasz_codes"].append("Nie znaleziono")
