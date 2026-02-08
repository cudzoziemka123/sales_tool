from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
from time import sleep
from file_interpeter import *
from env import set_env_var
import os



# LOG IN
def login_samasz(driver,company,email, password):
    # COMPLETE LOG IN FIELDS
    company_field = driver.find_element(By.ID, value="customerName-field")
    company_field.click()
    company_field.send_keys(company)
    employee_field = driver.find_element(By.ID, value= "userName-field")
    employee_field.click()
    employee_field.send_keys(email)
    password_field = driver.find_element(By.ID, value= "password-field")
    password_field.click()
    password_field.send_keys(password)
    sleep(5)

    # CHECK-IN TERMS
    terms_check = driver.find_elements(By.CLASS_NAME, value="ti-check")
    for check in terms_check:
        check.click()
    sleep(3)

    # CLICK LOG IN BUTTON
    log_on_btn = driver.find_element(By.CLASS_NAME, value="primary-action")
    log_on_btn.click()
    sleep(5)



# FUNCTION SEARCH FOR A PRICE TO THE SPECIFIC CODE, CREATES A LIST OF CODES AND PRICES
def find_code_return_price(code,driver,data):
    search_field = driver.find_element(By.ID, value="searchPhrase-field")
    search_field.click()
    sleep(5)
    search_field.clear()
    search_field.send_keys(code, Keys.ENTER)
    sleep(6)
    try:
        price=driver.find_element(By.CLASS_NAME, value="basic-price")
        samasz_code = driver.find_element(By.CLASS_NAME, value="product-code")
        #TODO przeformatować cene na liczbę: zabrać "PLN" i zmienić na float
        # jeżeli chcemy przerabiać na cene dla klienta.
        data['prices'].append(price.text)
        data['samasz_codes'].append(samasz_code.text)
    except NoSuchElementException:
        data['prices'].append("Nie znaleziono")
        data['samasz_codes'].append("Nie znaleziono")


def do_samasz_quotaion(document,details):
    set_env_var()
    company=os.environ.get("SAMASZ_COMPANY")
    email=os.environ.get("SAMASZ_LOGIN")
    password=os.environ.get("SAMASZ_PASSWORD")

    data=prepare_data(document,details['brand'])
    driver=set_webdriver_options()
    driver.get("https://kontrahenci.samasz.pl/login")
    sleep(5)

    login_samasz(driver, company, email, password)
    sleep(5)

    for part_code in data['codes']:
        find_code_return_price(part_code, driver,data)


    driver.quit()

    file_name=create_quotation_file(data, document)
    return file_name


