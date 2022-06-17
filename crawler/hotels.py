from selenium.webdriver.support import expected_conditions as ec
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent
from pymongo import MongoClient
from dotenv import load_dotenv
import time
import os
import threading
import queue


load_dotenv()
client = MongoClient(f"{os.getenv('host')}:27017",
                     username=os.getenv('mongouser'),
                     password=os.getenv('password'),
                     authMechanism=os.getenv('authMechanism')
                     )

user_agent = UserAgent().random
options = Options()
options.page_load_strategy = 'eager'
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-extensions')
chrome_options.add_argument('--profile-directory=Default')
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--disable-plugins-discovery")
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("window-size=1440,900")
chrome_options.add_argument(f'user-agent={user_agent}')


def get_divisions():
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
    driver.delete_all_cookies()
    URL_LOC = 'https://zh.wikipedia.org/wiki/中華民國臺灣地區鄉鎮市區列表'
    driver.get(URL_LOC)
    div = driver.find_elements(By.XPATH, "//div[@id='mw-content-text']/div[1]/table[7]/tbody/tr/td[1]/small")
    divisions = [x.text for x in div]
    divisions = set(divisions)
    driver.quit()
    return divisions


class Worker(threading.Thread):
    def __init__(self, worker_num, driver):
        threading.Thread.__init__(self)
        self.worker_num = worker_num
        self.driver = driver

    def run(self):
        while not job_queue.empty():
            self.hotelcom(job_queue.get())

    def hotelcom(self, div):
        col = client['personal_project']['hotelcom']
        URL = f'https://tw.hotels.com/Hotel-Search?destination={div}&startDate=2022-10-01&endDate=2022-10-02&rooms=1&adults=1'
        self.driver.get(URL)
        action = ActionChains(self.driver)
        foot = self.driver.find_element(By.TAG_NAME, "footer")
        while True:
            try:
                action.move_to_element(foot).perform()
                elm = WebDriverWait(self.driver, 15).until(
                    ec.presence_of_element_located((By.XPATH, "//button[@data-stid='show-more-results']"))
                )
                elm.click()
                time.sleep(0.5)
            except TimeoutException:
                cards = self.driver.find_elements(By.XPATH, "//section[@class='results']/ol/li[@data-stid='property-listing']")
                break
        print('scan_done')
        hotel_ls = []
        for c in cards:
            try:
                pack = self.fetch(c)
            except WebDriverException:
                driver.refresh()
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                driver.refresh()
                pack = self.fetch(c)
            hotel_ls.append(pack)
        col.insert_many(hotel_ls, bypass_document_validation=True)
        print(f'{div}: done at {time.perf_counter()}')

    def fetch(self, c):
        c.click()
        self.driver.switch_to.window(self.driver.window_handles[1])
        detail_elm = WebDriverWait(self.driver, 20).until(
            ec.presence_of_element_located((By.XPATH, "//div[@data-stid='content-hotel-title']"))
        )
        detail = detail_elm.text
        url = self.driver.current_url
        try:
            rating = self.driver.find_element(By.XPATH, "//div[@itemprop='aggregateRating']").text
        except NoSuchElementException:
            rating = 'non-provided'
        try:
            address = self.driver.find_element(By.XPATH, "//div[@itemprop='address']").text
        except NoSuchElementException:
            address = 'non-provided'
        try:
            img = self.driver.find_element(By.XPATH, "//div[@id='Overview']").\
                              find_element(By.TAG_NAME, 'img').get_attribute('src')
        except NoSuchElementException:
            img = 'non-provided'
        pack = {
            'detail': detail,
            'url': url,
            'rating': rating,
            'address': address,
            'img': img
        }
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return pack


if __name__ == '__main__':
    division = get_divisions()
    job_queue = queue.Queue()
    for job_index in division:
        job_queue.put(job_index)

    workers = []
    worker_count = 2
    for i in range(worker_count):
        num = i+1
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        driver.delete_all_cookies()
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

