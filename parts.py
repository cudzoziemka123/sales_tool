from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from time import sleep
import os

from file_interpeter import set_webdriver_options, prepare_data, create_quotation_file
from env import set_env_var


def login_to_account(driver,login,password):
    login_link = driver.find_element(By.CLASS_NAME, value="loginLink")
    login_link.click()

    login_field = driver.find_element(By.ID, "login_modal")
    login_field.click()
    login_field.send_keys(login)

    password_field = driver.find_element(By.ID, "pass_modal")
    password_field.click()
    password_field.send_keys(password)

    login_btn = driver.find_element(By.ID, "go_modal")
    login_btn.click()
    sleep(3)


def find_the_price(code,driver):
    search_field = driver.find_element(By.ID, "pcode")
    search_field.click()
    search_field.clear()
    search_field.send_keys(f"{code}", Keys.ENTER)

def find_price_by_code(driver,data):
    price = driver.find_element(By.CLASS_NAME, "bestOfferPrice")
    data['prices'].append(price.text.split(" ")[0])

def find_price_by_brand(brand,driver,data):
    # TODO Sprawdź czy działa (sprawdza nie tylko pierwszy case a wszystkie)
    case_brands = driver.find_elements(By.CLASS_NAME, "caseBrand")
    case_code = driver.find_element(By.CLASS_NAME, "casePartCode")
    for case_brand in case_brands:
        if case_brand.text.lower() == brand.lower():
            case_code.click()
            sleep(3)
            find_price_by_code(driver,data)
        else:
            data['prices'].append("Brak ceny")

# WYSZUKIWANIE
def return_price_list(brand,driver,data):
    for code in data['codes']:
        find_the_price(code,driver)
        sleep(3)
        try:
            find_price_by_code(driver,data)
        except NoSuchElementException:
            try:
                find_price_by_brand(brand,driver,data)
            except NoSuchElementException:
                data['prices'].append("Brak ceny")
        sleep(3)

def do_another_quotation(filename, details):
    set_env_var()
    login = os.getenv('PARTS_LOGIN')
    password = os.getenv('PARTS_PASSWORD')

    driver = set_webdriver_options()
    data=prepare_data(filename,details['brand'])
    driver.get("https://0parts.com/")
    sleep(2)

    login_to_account(driver,login, password)
    sleep(3)

    return_price_list(details['brand'],driver,data)
    file_name = create_quotation_file(data,filename)
    sleep(3)

    driver.quit()
    return file_name

