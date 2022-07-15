from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, \
    StaleElementReferenceException, ElementClickInterceptedException, InvalidArgumentException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium import webdriver

from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests

user_agent = UserAgent(verify_ssl=False).random
options = Options()
options.page_load_strategy = 'eager'
options = webdriver.ChromeOptions()
options.add_argument('--disable-extensions')
options.add_argument('--profile-directory=Default')
options.add_argument("--incognito")
options.add_argument("--disable-plugins-discovery")
options.add_argument("--start-maximized")
options.add_argument("--window-size=1440,900")
options.add_argument("--Zoom 60%")
options.add_argument(f'--user-agent={user_agent}')
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')
options.add_argument("–-Referer=https://www.facebook.com")
options.add_argument('--hide-scrollbars')
options.add_argument('--log-level=0')
options.add_argument('--ignore-certificate-errors')
options.add_argument("--content-type=text/plain")
options.add_argument("--content-encoding=gzip")
options.add_argument('--content-language: zh-TW')
options.add_argument('--charset=utf-8')
options.add_argument("-–disable-blink-features")
options.add_argument("-–disable-blink-features=AutomationControlled")
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--disable-application-cache")
options.add_argument("--disk-cache-size=0")
options.binary_location = '/usr/bin/google-chrome-beta'
# options.binary_location = '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta'

headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "utf-8",
    "Accept-Language": "zh-TW,zh;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": user_agent
}

# options.add_argument('--enable-logging')
# options.add_argument('--data-path=tmp/data-path')
# options.add_argument('--disk-cache-dir=tmp/cache-dir')
# options.add_argument('--user-data-dir=tmp/user-data')

