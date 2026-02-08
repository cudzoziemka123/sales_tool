import os

from env import set_env_var
from file_interpeter import*

from selenium.webdriver.common.by import By

from selenium.common.exceptions import NoSuchElementException
from time import sleep
from selenium.webdriver.common.keys import Keys


def accept_cookies_modal(driver):
    modal=driver.switch_to.active_element
    for i in range (4):
        modal.send_keys(Keys.TAB)
    modal.send_keys(Keys.ENTER)

def login_krone(driver,login,password):
    driver.find_element(By.ID, "aiLoginBtn").click()
    login_field=driver.find_element(By.ID, "username")
    login_field.click()
    login_field.send_keys(login)

    password_field=driver.find_element(By.ID, "password")
    password_field.click()
    password_field.send_keys(password)

    driver.find_element(By.CSS_SELECTOR,"button.button").click()
    sleep(3)


def find_code_return_price(driver,data):
    for code in data['codes']:
        search_field = driver.find_element(By.CLASS_NAME, value='ai-search-input')
        search_field.clear()
        search_field.click()
        search_field.send_keys(code, Keys.ENTER)
        sleep(3)
        try:
            price_field = driver.find_element(By.CLASS_NAME, value='ai-price-value')

            if price_field.text == "Price on request":
                tile = driver.find_element(By.CLASS_NAME, value='ai-product-tile')
                tile.click()
                sleep(3)
                price_field = driver.find_element(By.CLASS_NAME, value='ai-price-value')
                data['prices'].append(price_field.text.split(" ")[0])
            else:
                data['prices'].append(price_field.text.split(" ")[0])
        except NoSuchElementException:
            data['prices'].append('Not found')

def do_krone_quotation(filename, details):
    set_env_var()
    login=os.environ.get('KRONE_LOGIN')
    password=os.environ.get('KRONE_PASSWORD')

    data = prepare_data(filename, details['brand'])

    my_driver = set_webdriver_options()
    my_driver.get("https://dealershop.agroparts.com/ads/ads-client/search/krone/igl-agrartechnik")
    sleep(2)

    accept_cookies_modal(my_driver)
    login_krone(my_driver,login,password)
    find_code_return_price(my_driver,data)
    file_name = create_quotation_file(data,"Krone_test.xlsx")

    my_driver.quit()
    return file_name







