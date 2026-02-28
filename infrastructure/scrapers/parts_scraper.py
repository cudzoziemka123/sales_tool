"""
Scraper cen z portalu 0parts.com.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException


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
    WebDriverWait(driver, 15).until(EC.staleness_of(login_btn))


def warmup_parts(driver) -> None:
    """
    Warm-up after login: ensure search field is ready.
    """
    field = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.ID, "pcode"))
    )
    field.click()
    field.clear()


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


def _normalize_code(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _get_price_by_brand(driver, brand: str, target_code: str, data: dict) -> None:
    """
    Fallback: finds row by brand + expected code and clicks matching part code.
    """
    lines = driver.find_elements(By.CLASS_NAME, value="startSearching")
    target_brand = brand.lower().strip()
    target_code_norm = _normalize_code(target_code)

    # 1) Prefer exact row match by both brand and code.
    for line in lines:
        try:
            case_brand = line.find_element(By.CLASS_NAME, value="caseBrand")
            case_code = line.find_element(By.CLASS_NAME, value="casePartCode")
        except NoSuchElementException:
            continue
        case_brand_norm = case_brand.text.lower().strip()
        case_code_norm = _normalize_code(case_code.text)
        if case_brand_norm == target_brand and (
            case_code_norm == target_code_norm
            or target_code_norm in case_code_norm
            or case_code_norm in target_code_norm
        ):
            case_code.click()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "bestOfferPrice"))
            )
            _get_price_by_code(driver, data)
            return
        else:
            continue

    # 2) If code mapping is not possible, fallback to first brand row.
    for line in lines:
        try:
            case_brand = line.find_element(By.CLASS_NAME, value="caseBrand")
        except NoSuchElementException:
            continue
        if case_brand.text.lower().strip() == target_brand:
            try:
                case_code = line.find_element(By.CLASS_NAME, value="casePartCode")
            except NoSuchElementException:
                continue
            case_code.click()
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "bestOfferPrice"))
            )
            _get_price_by_code(driver, data)
            return

    data["prices"].append("Brak ceny")


def scrape_prices(driver, brand: str, data: dict) -> None:
    """Wyszukuje ceny dla kodów z data['codes'] i uzupełnia data['prices']."""
    for code in data["codes"]:
        _find_price(driver, code)

        # If list rows are present (often multiple brands), always resolve by row/brand.
        rows = driver.find_elements(By.CLASS_NAME, value="startSearching")
        if rows:
            try:
                _get_price_by_brand(driver, brand, code, data)
            except NoSuchElementException:
                data["prices"].append("Brak ceny")
            continue

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "bestOfferPrice"))
            )
            _get_price_by_code(driver, data)
        except (NoSuchElementException, TimeoutException):
            data["prices"].append("Brak ceny")
