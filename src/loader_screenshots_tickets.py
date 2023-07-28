from selenium import webdriver
import time
import random
import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class ScreenshotsAviasales():
    def __init__(self):
        self.options = webdriver.ChromeOptions()
        self.browser = webdriver.Chrome(options=self.options)

    def makes_screenshot_of_specific_ticket(self, url):
        self.browser.get(url)
        wait = WebDriverWait(self.browser, 7)
        wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ticket-desktop__body")))
        time.sleep(2)
        try:
            element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "highlighted-ticket")))
            element.screenshot("screenshot.png")
        except:
            try:
                element = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "ticket-main-modal__itinerary-info-inner")))
                element.screenshot("screenshot.png")
            except:
                print('Не получилсоь')
                self.browser.quit()

screen = ScreenshotsAviasales()
saved_screen = screen.makes_screenshot_of_specific_ticket('https://www.aviasales.ru/search/MOW0110EVN1?t=3F16961784001696190100000195DMEEVN_652b68ff686e3e30cd21414027878e71_11349&search_date=25072023&expected_price_uuid=9e8914e6-6859-4f34-b5ae-0642fe57a341&expected_price_source=share&expected_price_currency=rub&expected_price=11349')
