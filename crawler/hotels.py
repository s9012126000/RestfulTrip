from config.mongo_config import *
from config.crawler_config import *
import threading
import datetime
import queue
import time
import json


class Worker(threading.Thread):
    def __init__(self, worker_num, driver):
        threading.Thread.__init__(self)
        self.worker_num = worker_num
        self.driver = driver

    def run(self):
        while not job_queue.empty():
            self.hotelcom(job_queue.get())

    def hotelcom(self, div):
        col = client['personal_project']['hotels']
        URL = f'https://tw.hotels.com/Hotel-Search?destination={div}&startDate=2022-10-01&endDate=2022-10-02&rooms=1&adults=1'
        self.driver.get(URL)
        print(f"{self.worker_num}", URL)
        original_window = driver.current_window_handle
        action = ActionChains(self.driver)

        def get_cards():
            last_len = 0
            while True:

                self.driver.execute_script("window.scrollTo(0, 500000)")
                button = WebDriverWait(self.driver, 5).until(
                    ec.element_to_be_clickable((By.XPATH, "//button[@data-stid='show-more-results']"))
                )
                action.move_to_element(button).perform()
                time.sleep(2)
                button.click()
                time.sleep(1)
                check = len(self.driver.find_elements(By.XPATH, "//section[@class='results']/ol/li"))
                if check > last_len:
                    last_len = check
                elif check == last_len:
                    break
            card = self.driver.find_elements(
                By.XPATH, "//section[@class='results']/ol/li/div/a[@data-stid='open-hotel-information']")
            return card
        try:
            cards = get_cards()
        except:
            cards = self.driver.find_elements(
                By.XPATH, "//section[@class='results']/ol/li/div/a[@data-stid='open-hotel-information']")
            print(f'division {div} fail')
        cards = [x.get_attribute('href') for x in cards]
        print(f"worker {self.worker_num}: <<{div}>> {len(cards)} cards \n-------------------------------")
        hotel_ls = []
        print(len(driver.window_handles))
        while len(driver.window_handles) > 1:
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.close()
            self.driver.switch_to.window(original_window)
        for c in range(len(cards)):
            try:
                pack = self.fetch(cards[c], c)
            except:
                continue
            hotel_ls.append(pack)
        col.insert_many(hotel_ls, bypass_document_validation=True)

    def fetch(self, url, n):
        self.driver.execute_script("window.open()")
        WebDriverWait(self.driver, 10).until(ec.number_of_windows_to_be(2))
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)
        time.sleep(1)
        self.driver.switch_to.window(self.driver.window_handles[1])
        detail_elm = WebDriverWait(self.driver, 60).until(
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
        name = detail.split('\n')[0]
        print(f"worker {self.worker_num}: {n} {name}")
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return pack


if __name__ == '__main__':
    START_TIME = datetime.datetime.now()
    print(f"hotels started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    with open('jsons/divisions.json') as f:
        divisions = json.load(f)
    job_queue = queue.Queue()
    for job_index in divisions:
        job_queue.put(job_index)

    workers = []
    worker_count = 5
    for i in range(worker_count):
        num = i+1
        driver = webdriver.Chrome(ChromeDriverManager(version='104.0.5112.20').install(), options=options)
        driver.delete_all_cookies()
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
        worker.driver.quit()
        print(f'{worker.worker_num} done')

    END_TIME = datetime.datetime.now()
    print(f"hotels started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"hotels finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"hotels cost {(END_TIME-START_TIME).seconds//60} minutes")
