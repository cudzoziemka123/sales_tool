"""
Scraper cen z portalu Krone (dealershop.agroparts.com).
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
)
from time import sleep

logger = logging.getLogger(__name__)


def accept_cookies_modal(driver) -> None:
    """Obsługa modala cookies (stary, sprawdzony wariant)."""
    try:
        modal = driver.switch_to.active_element
        for _ in range(4):
            modal.send_keys(Keys.TAB)
        modal.send_keys(Keys.ENTER)
    except Exception:
        # Keep flow non-blocking when modal is already closed or not focused.
        pass


def login_krone(driver, login: str, password: str) -> None:
    """Logowanie na portal Krone."""
    login_btn = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "aiLoginBtn"))
    )
    login_btn.click()
    login_field = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "username"))
    )
    login_field.click()
    login_field.send_keys(login)

    password_field = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.ID, "password"))
    )
    password_field.click()
    password_field.send_keys(password)

    submit_btn = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button"))
    )
    submit_btn.click()

    # Login is considered complete only when BOTH conditions are met:
    # 1) search input is interactable
    # 2) login form is no longer visible (username field hidden/removed)
    def _login_completed(drv):
        try:
            search_ready = drv.find_element(
                By.CLASS_NAME, "ai-search-input").is_enabled()
        except Exception:
            search_ready = False

        try:
            username_visible = drv.find_element(
                By.ID, "username").is_displayed()
        except Exception:
            username_visible = False

        return search_ready and not username_visible

    try:
        WebDriverWait(driver, 60).until(_login_completed)
    except TimeoutException:
        # One extra submit attempt helps when portal does partial auth redirect.
        try:
            submit_btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button"))
            )
            submit_btn.click()
        except Exception:
            pass
        WebDriverWait(driver, 60).until(_login_completed)


def warmup_krone(driver) -> None:
    """
    Warm-up after login: ensure search input is stable and clickable.
    """
    field = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "ai-search-input"))
    )
    _wait_spinner_gone(driver, timeout=20)
    _safe_click(driver, field)
    field.clear()
    sleep(1)


def _read_price_text(driver) -> str | None:
    try:
        price_field = driver.find_element(
            By.CLASS_NAME, value="ai-price-value")
        text = (price_field.text or "").strip()
        return text or None
    except NoSuchElementException:
        return None


def _wait_for_price_refresh(
    driver,
    previous_price: str | None,
    timeout: int = 10,
    poll_seconds: float = 0.5,
) -> str | None:
    elapsed = 0.0
    stable_hits = 0
    last_seen = None

    while elapsed < timeout:
        try:
            current = _read_price_text(driver)
        except StaleElementReferenceException:
            current = None

        if current is None:
            sleep(poll_seconds)
            elapsed += poll_seconds
            continue

        if previous_price is not None and current != previous_price:
            return current

        # When previous_price is None (first query), require brief stability.
        if previous_price is None:
            if current == last_seen:
                stable_hits += 1
                if stable_hits >= 2:
                    return current
            else:
                stable_hits = 0
                last_seen = current

        sleep(poll_seconds)
        elapsed += poll_seconds

    return None


def _resolve_price_text(driver, timeout: int = 10) -> str | None:
    """
    Resolves final price text. If tile shows 'Price on request', opens details first.
    """
    price_text = _wait_for_price_refresh(
        driver, previous_price=None, timeout=timeout)
    if price_text is None:
        return None

    if price_text == "Price on request":
        for _ in range(2):
            try:
                tile = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "ai-product-tile"))
                )
                tile.click()
                detailed = _wait_for_price_refresh(
                    driver,
                    previous_price="Price on request",
                    timeout=timeout,
                )
                if detailed is not None:
                    return detailed
            except (TimeoutException, StaleElementReferenceException):
                continue
        return None

    return price_text


def scrape_prices(driver, data: dict) -> None:
    """Wyszukuje ceny dla kodów z data['codes'] i uzupełnia data['prices']."""
    for code in data["codes"]:
        logger.info("Krone scrape code=%s", code)
        result_price = None
        for attempt in range(3):
            previous_price = _read_price_text(driver)
            search_field = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ai-search-input"))
            )
            _wait_spinner_gone(driver, timeout=20)
            search_field.clear()
            _safe_click(driver, search_field)
            search_field.send_keys(code, Keys.ENTER)

            # First, wait for generic refresh from previous state.
            refreshed = _wait_for_price_refresh(
                driver,
                previous_price=previous_price,
                timeout=10 if attempt == 0 else 20,
            )
            if refreshed is None:
                sleep(1)
                continue

            # Then resolve final value (handles "Price on request" path).
            final_text = _resolve_price_text(driver, timeout=10)
            if final_text is None:
                # fallback to refreshed text when detail view could not be opened
                final_text = refreshed

            result_price = final_text
            break
            # Note: Stale element may happen between refreshes; retry next attempt.
        if result_price is None:
            try:
                # quick recovery for stale UI state between codes
                field = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CLASS_NAME, "ai-search-input"))
                )
                field.click()
            except (TimeoutException, StaleElementReferenceException):
                pass

        if result_price is None:
            data["prices"].append("Not found")
        else:
            data["prices"].append(result_price.split(" ")[0])


def _wait_spinner_gone(driver, timeout: int = 20) -> None:
    selectors = [
        "div.spinner-wrapper.ng-star-inserted",
        ".spinner-wrapper",
        ".spinner-loader",
    ]
    for css in selectors:
        try:
            WebDriverWait(driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, css))
            )
            return
        except TimeoutException:
            continue


def _safe_click(driver, element) -> None:
    try:
        element.click()
    except ElementClickInterceptedException:
        _wait_spinner_gone(driver, timeout=20)
        try:
            element.click()
        except ElementClickInterceptedException:
            logger.warning(
                "Krone click intercepted again, using JS click fallback")
            driver.execute_script("arguments[0].click();", element)
