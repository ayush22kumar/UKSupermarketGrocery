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
from commons.configs import DATADIR_PATH


class BaseCollector(object):

    def __init__(self):
        pass

    def get_driver(self):
        options = Options()
        options.headless = True
        options.add_argument("--headless")

        return webdriver.Firefox(options=options)


