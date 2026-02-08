import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from time import sleep
import pandas as pd
from file_interpeter import set_webdriver_options, prepare_data, prepare_data_kv
from env import set_env_var

# LOG IN
def login_kv(driver,email,password):
    btn = driver.find_element(by=By.CLASS_NAME, value="btn-primary")
    btn.click()
    sleep(5)

    email_field = driver.find_element(by=By.NAME, value="Email Address")
    email_field.click()
    email_field.send_keys(f"{email}")

    password_field = driver.find_element(by=By.NAME, value="Password")
    password_field.click()
    password_field.send_keys(f"{password}")

    login_btn = driver.find_element(by=By.ID, value="next")
    login_btn.click()
    sleep(8)

# SEARCH CODES
def find_code(driver,data):
    search_field = driver.find_element(by=By.CLASS_NAME, value="searchBar")
    search_field.click()
    search_field.send_keys(f"{data}", Keys.ENTER)
    sleep(2)
    driver.find_element(by=By.CLASS_NAME, value="submitButton").click()

    # POZYSKANIE DANYCH
    sleep(60)
    # TODO Tu można dać if-a żeby czekał aż wszystko się załaduje.

# CODE LIST CREATING
def create_codes_list(driver):
    codes_web_list = driver.find_elements(by=By.CLASS_NAME, value="warehouseName")
    part_codes_list = [code.text for code in codes_web_list]
    print(part_codes_list)
    return part_codes_list
#
# CHECK IN IF THE CODES CAN BE FOUND ON THE PAGE
def delete_wrong_codes(driver):
    is_it_valid_web_list = driver.find_elements(by=By.CLASS_NAME, value="card-title")
    is_it_valid_list = [title.text for title in is_it_valid_web_list]
    print(is_it_valid_list)
    return is_it_valid_list


# CREATING QTY LIST
def create_qty_list(driver):
    qty_web_list = driver.find_elements(by=By.ID, value="atpQuantity")
    quantity_list = [qty.text for qty in qty_web_list]
    return quantity_list

# REDUCING CODE LIST WITH CHECKED WITH WEB PAGE LIST OF CODES
def reduce_codes_list(valid_codes_list,codes_list):
    index = 0
    for title in valid_codes_list:
            if title == "NOT FOUND":
                del codes_list[index]
                index = index - 1
            index = index + 1
    return codes_list

# CREATING LIST OF PRICES WITH DATA FROM THE PAGE
def create_price_list(driver):
    details_list = driver.find_elements(by=By.CSS_SELECTOR, value='td.materialCardResult div')
    prices_from_web_list =[]

    for detail in details_list:
        if "PLN" in detail.text:
            price_without_currency = detail.text.split(" ")[0]
            price_without_dots = price_without_currency.replace(".", "")
            # float_price = price_without_dots.replace(",", ".")
            price_for_client = price_without_dots
            # price_for_client = str(round(((float(float_price)-float(float_price)*sale)/euro)*mark_up,2)).replace(".", ",")
            prices_from_web_list.append(price_for_client)
    return prices_from_web_list

# CREATING EXCEL FILE BASED ON DATA FROM THE PAGE
def create_quotation_file(codes_list,qty_list,price_list, document_name):
    quotation = pd.DataFrame(
        {"Code": codes_list, "Quantity": qty_list, "Price": price_list}
    )
    file_name = f"{document_name}_quotation.xlsx"
    quotation.to_excel(f"for_client/{document_name}", index=False)
    return file_name


def do_kv_quotation(document, details):
    set_env_var()
    email=os.getenv('KV_LOGIN')
    password = os.getenv('KV_PASSWORD')
    data = prepare_data_kv(document)

    my_driver = set_webdriver_options()
    my_driver.get("https://www.kvgportal.com/AtpCheck/")
    sleep(3)

    login_kv(my_driver,email,password)
    find_code(my_driver,data)

    excel_codes_list = create_codes_list(my_driver)
    web_codes_list = delete_wrong_codes(my_driver)
    codes_list = reduce_codes_list(excel_codes_list,web_codes_list)

    qty_list = create_qty_list(my_driver)
    price_list = create_price_list(my_driver)

    file_name=create_quotation_file(codes_list, qty_list, price_list, document)
    my_driver.quit()
    return file_name

