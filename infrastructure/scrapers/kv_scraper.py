"""
Scraper cen z portalu Kverneland (kvgportal.com/AtpCheck).
"""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from time import sleep

logger = logging.getLogger(__name__)


def login_kv(driver, email: str, password: str) -> None:
    """Logowanie na portal Kverneland."""
    logger.warning("KV login: start")
    btn = driver.find_element(By.CLASS_NAME, value="btn-primary")
    btn.click()

    email_field = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.NAME, "Email Address"))
    )
    email_field.click()
    email_field.send_keys(email)

    password_field = driver.find_element(By.NAME, value="Password")
    password_field.click()
    password_field.send_keys(password)

    login_btn = driver.find_element(By.ID, value="next")
    login_btn.click()
    WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "searchBar"))
    )
    logger.warning("KV login: searchBar visible")


def warmup_kv(driver) -> None:
    """
    Warm-up after login: verify key controls are interactable.
    """
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "searchBar"))
    )
    # Search is submitted by Enter, so we only ensure search field wrapper exists.
    sleep(1)
    logger.warning("KV warmup: done")


def search_codes(driver, data: str) -> None:
    """Wyszukuje kody na stronie ATP Check."""
    expected_items = len([ln for ln in data.splitlines() if ln.strip()])
    logger.warning(
        "KV search start: payload_chars=%s payload_lines=%s",
        len(data),
        expected_items,
    )
    # KV aggressively re-renders controls; retry full interaction when element goes stale.
    for attempt in range(4):
        try:
            logger.debug("KV search attempt=%s", attempt + 1)
            search_field = _resolve_search_input(driver)
            _fill_search_field(search_field, data)

            _submit_search(driver, search_field, attempt=attempt + 1)
            _wait_for_results_to_stabilize(
                driver,
                expected_items=expected_items,
                timeout_seconds=180,
                stable_checks=4,
            )
            logger.warning("KV search completed on attempt=%s", attempt + 1)
            return
        except (StaleElementReferenceException, TimeoutException):
            if attempt == 3:
                logger.exception("KV search failed after retries")
                raise
            logger.warning("KV search retry due to stale/timeout (attempt=%s)", attempt + 1)
            sleep(1)
            continue


def _submit_search(driver, search_field, attempt: int) -> None:
    """Submit KV search by pressing Enter in the resolved search field."""
    search_field.click()
    search_field.send_keys(Keys.ENTER)
    logger.warning("KV submit: ENTER sent (attempt=%s)", attempt)
    _confirm_submit_modal_if_present(driver, attempt)


def _confirm_submit_modal_if_present(driver, attempt: int) -> None:
    """
    After Enter KV may open a confirmation modal.
    Click its Submit button when present; otherwise continue.
    """
    selectors = [
        ".submitButton",
        "button[type='submit']",
        "button.btn-primary",
        "input[type='submit']",
    ]

    for _ in range(8):
        for selector in selectors:
            buttons = driver.find_elements(By.CSS_SELECTOR, selector)
            for button in buttons:
                try:
                    if not button.is_displayed() or not button.is_enabled():
                        continue
                    label = (
                        (button.text or "")
                        or (button.get_attribute("value") or "")
                    ).strip().lower()
                    if label and "submit" not in label:
                        continue
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", button
                    )
                    try:
                        button.click()
                    except Exception:
                        driver.execute_script("arguments[0].click();", button)
                    logger.warning("KV submit: modal submit clicked (attempt=%s)", attempt)
                    return
                except StaleElementReferenceException:
                    continue
        sleep(0.5)

    logger.warning("KV submit: modal submit not detected, continuing (attempt=%s)", attempt)


def _resolve_search_input(driver):
    """
    Resolve editable control used by KV search.
    In some UI states `.searchBar` is just a wrapper, not the real input.
    """
    wrapper = WebDriverWait(driver, 30).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "searchBar"))
    )
    wrapper.click()

    editable_candidates = wrapper.find_elements(
        By.CSS_SELECTOR,
        "input, textarea, [contenteditable='true']",
    )
    for candidate in editable_candidates:
        if candidate.is_displayed() and candidate.is_enabled():
            return candidate
    return wrapper


def _fill_search_field(search_field, data: str) -> None:
    """Fill KV multiline search field and verify payload is present."""
    tag_name = (search_field.tag_name or "").lower()
    payload_to_type = data
    if tag_name == "input":
        # Single-line inputs interpret newline as Enter; keep batch on one line.
        payload_to_type = " ".join(part for part in data.splitlines() if part.strip())

    search_field.click()
    try:
        search_field.clear()
    except Exception:
        # Some browser/DOM states expose non-standard clear behavior.
        pass

    search_field.send_keys(Keys.CONTROL, "a")
    search_field.send_keys(Keys.DELETE)
    search_field.send_keys(payload_to_type)

    typed = _read_field_text(search_field)
    if not typed:
        _set_field_text_with_js(search_field, payload_to_type)
        typed = _read_field_text(search_field)
    if not typed:
        raise TimeoutException("KV search field did not accept payload.")
    logger.debug("KV typed chars=%s", len(typed))


def _read_field_text(search_field) -> str:
    return (
        search_field.get_attribute("value")
        or search_field.get_attribute("textContent")
        or search_field.get_attribute("innerText")
        or ""
    ).strip()


def _set_field_text_with_js(search_field, data: str) -> None:
    driver = search_field.parent
    driver.execute_script(
        """
        const el = arguments[0];
        const value = arguments[1];
        const tag = (el.tagName || "").toLowerCase();
        const editable = el.getAttribute("contenteditable") === "true";
        if (tag === "input" || tag === "textarea") {
            el.value = value;
        } else if (editable) {
            el.textContent = value;
        }
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
        """,
        search_field,
        data,
    )


def _wait_for_results_to_stabilize(
    driver,
    expected_items: int,
    timeout_seconds: int = 180,
    stable_checks: int = 4,
    poll_seconds: float = 1.0,
) -> None:
    """
    Czeka, aż liczba wyników (`warehouseName`) przestanie się zmieniać.

    Strona KV dociąga wyniki partiami, więc samo pojawienie się pierwszego
    elementu to za mało. Kończymy dopiero, gdy licznik jest stabilny przez
    `stable_checks` kolejnych odczytów.
    """
    last_count = -1
    stable_counter = 0
    elapsed = 0.0

    while elapsed < timeout_seconds:
        # `warehouseName` can be empty when all items are NOT FOUND.
        # `card-title` appears for both found and not-found rows, so use both.
        warehouse_count = len(driver.find_elements(By.CLASS_NAME, value="warehouseName"))
        title_count = len(driver.find_elements(By.CLASS_NAME, value="card-title"))
        current_count = max(warehouse_count, title_count)
        min_required = 1 if expected_items <= 1 else 2

        if current_count < min_required:
            stable_counter = 0
            last_count = current_count
            sleep(poll_seconds)
            elapsed += poll_seconds
            continue

        if current_count > 0 and current_count == last_count:
            stable_counter += 1
            if stable_counter >= stable_checks:
                return
        else:
            stable_counter = 0
            last_count = current_count

        sleep(poll_seconds)
        elapsed += poll_seconds

    raise TimeoutException(
        "KV results did not stabilize within timeout "
        f"(warehouse={warehouse_count}, titles={title_count})."
    )


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
    result = []
    for idx, title in enumerate(titles_list):
        if title != "NOT FOUND" and idx < len(codes_list):
            result.append(codes_list[idx])
    return result


def reduce_list_by_titles(titles_list: list, values_list: list) -> list:
    """Redukuje dowolną listę według tych samych reguł NOT FOUND."""
    result = []
    for idx, title in enumerate(titles_list):
        if title != "NOT FOUND" and idx < len(values_list):
            result.append(values_list[idx])
    return result
