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

user_agent = UserAgent().random
options = Options()
# options.page_load_strategy = 'eager'
chrome_options = webdriver.ChromeOptions()
#chrome_options.add_argument('--disable-extensions')
#chrome_options.add_argument('--profile-directory=Default')
#chrome_options.add_argument("--incognito")
#chrome_options.add_argument("--disable-plugins-discovery")
chrome_options.add_argument("--start-maximized")
#chrome_options.add_argument("--window-size=1440,900")
#chrome_options.add_argument("Zoom 60%")
chrome_options.add_argument(f'--user-agent={user_agent}')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--no-sandbox')
# chrome_options.add_argument("–-Referer=https://www.facebook.com")
#chrome_options.add_argument('--user-data-dir=tmp/user-data')
#chrome_options.add_argument('--hide-scrollbars')
#chrome_options.add_argument('--enable-logging')
#chrome_options.add_argument('--log-level=0')
#chrome_options.add_argument('--ignore-certificate-errors')
#chrome_options.add_argument("--content-type=text/plain")
#chrome_options.add_argument("--content-encoding=gzip")
#chrome_options.add_argument('content-language: zh-TW')
chrome_options.add_argument('--charset=utf-8')
#chrome_options.add_argument("-–disable-blink-features")
#chrome_options.add_argument("-–disable-blink-features=AutomationControlled")
chrome_options.add_argument('--disable-dev-shm-usage') 
# chrome_options.add_argument('--v=99')
# chrome_options.add_argument('--single-process')
# chrome_options.add_argument('--data-path=tmp/data-path')
# chrome_options.add_argument('--homedir=tmp')
# chrome_options.add_argument('--disk-cache-dir=tmp/cache-dir')
# chrome_options.add_argument('--no-proxy-server')
# chrome_options.add_argument("--proxy-server='direct://'")
# chrome_options.add_argument("--proxy-bypass-list=*")

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

