from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.error import ContentTooShortError
from urllib3.exceptions import NewConnectionError, ConnectionError, MaxRetryError
import time
import pandas as pd
import os
import datetime
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.common.exceptions import NoSuchElementException
from random import randint
from selenium import webdriver
import re
from selenium.webdriver.firefox.options import Options
from commons.configs import DATADIR_PATH, MAX_PAGE_PER_CATEGORY
from base_collector import BaseCollector




class ALDICollector(BaseCollector):

    def __int__(self):
        super(ALDICollector, self).__init__()
        self.output_datadir = os.path.join(DATADIR_PATH, 'ALDI')
        try:
            os.makedirs(self.output_datadir)
        except:
            pass
        self.sleep_time = 10
        self.categories = ['frozen', 'chilled-food']
        self.base_url = 'https://groceries.aldi.co.uk/en-GB'
        self.max_page_limit_per_category = MAX_PAGE_PER_CATEGORY
        self.css_elements_map = {
            'last_page_number': 'ul .d-flex-inline.pt-2',
            'product_name': '#vueSearchResults .p.text-default-font',
            'product_price': '#vueSearchResults div.product-tile-price.text-center > div > span > span',
            'product_price_per_kg': '#vueSearchResults div.product-tile-price.text-center > div > div > p > small > span',
        }


    def scrape(self):

        out_file_time = str(datetime.datetime.now())
        out_file_time = out_file_time.replace(' ', '').replace('.','').replace(':','')
        output_file = os.path.join(self.output_datadir, 'raw_data_{0}'.format(out_file_time + '.csv'))

        dataset = []

        for _category in self.categories:
            print('Working on Category {0}'.format(_category))
            last_page_number = self._get_last_page_number(f'{self.base_url}/{_category}')

            print('Found pages for category {0} -> {1}'.format(_category, last_page_number))

            page = 1
            while page <= last_page_number:

                print('Running Page Number {0} for category {1}'.format(page, _category))

                driver = self.get_driver()

                try:
                    driver.get(f'{self.base_url}/{_category}?&page={page}')
                    time.sleep(randint(2, 5))

                    raw_names = driver.find_elements(By.CSS_SELECTOR, self.css_elements_map['product_name'])
                    prices = driver.find_elements(By.CSS_SELECTOR, self.css_elements_map['product_price'])
                    price_per_kg = driver.find_elements(By.CSS_SELECTOR, self.css_elements_map['product_price_per_kg'])
                    page_number = [page] * len(raw_names)

                    price_regex = re.compile(r'[^\d.,]+')

                    names = map(lambda x: x.text, raw_names)
                    names_hrefs = map(lambda x: x.get_attribute('href'), raw_names)
                    prices = map(lambda x: x.text, prices)
                    prices = map(lambda x: price_regex.sub('', x), prices)
                    price_per_kg = map(lambda x: x.text, price_per_kg)
                    price_per_kg = map(lambda x: x.replace(u'\xA3', ''), price_per_kg)

                    category_list = [_category] * len(raw_names)

                    page_product_data = list(zip(page_number, names, prices, price_per_kg, names_hrefs, category_list))
                    dataset.extend(page_product_data)

                    page +=1
                except (TimeoutException, WebDriverException,
                        ConnectionError, NewConnectionError, MaxRetryError, TimeoutError,
                        ContentTooShortError) as exc:
                    driver.quit()
                    print('Found error in page {0}', page)
                    #Page could not be fetched, restart driver again
                    driver = self.get_driver()
                    continue

                driver.quit()

        df = pd.DataFrame(dataset, columns =['Page Number', 'Product Name', 'Price',
                                             'Price_per_KG', 'Product HREF', 'Category'])
        df.to_csv(output_file, index=False)

    def _get_last_page_number(self, url_to_fetch):

        driver = self.get_driver()
        driver.get(url_to_fetch)
        time.sleep(self.sleep_time)
        last_page_css = self.css_elements_map['last_page_number']
        try:
            last_page_number = driver.find_element(By.CSS_SELECTOR, last_page_css).text
            last_page_number = last_page_number.replace('of', '').replace(' ', '')
            last_page_number = int(last_page_number)
        except NoSuchElementException:
            last_page_number = 1
            driver.quit()

        except (TimeoutException, WebDriverException, ValueError,
                ConnectionError, NewConnectionError, MaxRetryError, TimeoutError, ContentTooShortError):
            driver.quit()
            #try again with a timeout
            driver1 = self.get_driver()
            driver1.get(f'{self.base_url}/search/{url_to_fetch}')
            wait = WebDriverWait(driver1, 30)  # Wait for a maximum of 30 seconds
            time.sleep(self.sleep_time)
            last_page_number = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, last_page_css))).text
            last_page_number = last_page_number.replace('of', '').replace(' ', '')
            last_page_number = int(last_page_number)
            driver1.quit()

        if self.max_page_limit_per_category and int(last_page_number) > self.max_page_limit_per_category:
            return self.max_page_limit_per_category
        return int(last_page_number)

if __name__ == "__main__":
    x = ALDICollector()
    x.__int__()
    x.scrape()