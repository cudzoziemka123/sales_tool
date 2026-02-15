"""
Fabryka WebDriver Chrome – konfiguracja i tworzenie instancji.
"""

from selenium import webdriver


def create_chrome_driver(detach: bool = True):
    """Tworzy instancję Chrome WebDriver z opcją detach."""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", detach)
    return webdriver.Chrome(options=chrome_options)
