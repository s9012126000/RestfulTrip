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

    def run_function_with_retry(self, func, parm, err, msg):
        result = None
        tag = False
        try:
            result = func(*parm)
        except err:
            for i in range(5):
                try:
                    time.sleep(1)
                    self.driver.refresh()
                    result = func(*parm)
                    break
                except err:
                    print(
                        f"[{datetime.datetime.now().isoformat()}] worker {self.worker_num}, attempt {i + 1} {msg} fail")
                    if i == 4:
                        with open("logs/hotels/hotels_crawler.log", "a") as e:
                            message = f'[{datetime.datetime.now().isoformat()}][{err.__name__}]: {msg} fail\n'
                            print(message)
                            e.write(message)
                        tag = True
        return result, tag

    def get_hotel_cards(self):
        last_len = 0
        while True:
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 50000)")
            button = WebDriverWait(self.driver, 5).until(
                ec.element_to_be_clickable((By.XPATH, "//button[@data-stid='show-more-results']"))
            )
            time.sleep(3)
            button.click()
            time.sleep(1)
            check = len(self.driver.find_elements(By.XPATH, "//section[@class='results']/ol/li"))
            if check > last_len:
                last_len = check
            elif check == last_len:
                break
        card = self.driver.find_elements(
            By.XPATH, "//section[@class='results']/ol/li/div/a[@data-stid='open-hotel-information']",
        )
        return card

    def remove_redundant_window(self):
        while len(self.driver.window_handles) > 1:
            print(f"duplicate window occur: {len(self.driver.window_handles)}")
            self.driver.switch_to.window(self.driver.window_handles[1])
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

    def fetch_data(self, url, n, hotel_ls):
        self.driver.get(url)
        detail_elm = WebDriverWait(self.driver, 15).until(
            ec.presence_of_element_located((By.XPATH, "//div[@data-stid='content-hotel-title']"))
        )
        detail = detail_elm.text
        url = self.driver.current_url
        try:
            rating = self.driver.find_element(By.XPATH, "//div[@itemprop='aggregateRating']").text
        except NoSuchElementException:
            rating = "non-provided"
        try:
            address = self.driver.find_element(By.XPATH, "//div[@itemprop='address']").text
        except NoSuchElementException:
            address = "non-provided"
        try:
            img = self.driver.find_element(By.XPATH, "//div[@id='Overview']")\
                .find_element(By.TAG_NAME, "img").get_attribute("src")
        except NoSuchElementException:
            img = "non-provided"
        pack = {
            "detail": detail,
            "url": url,
            "rating": rating,
            "address": address,
            "img": img,
        }
        name = detail.split("\n")[0]
        print(f"worker {self.worker_num}: {n} {name}")
        hotel_ls.append(pack)

    def get_hotelcom_hotels(self, div):
        url = f"https://tw.hotels.com/Hotel-Search?destination={div}&startDate=2022-10-01&endDate=2022-10-02&rooms=1&adults=1"
        self.driver.get(url)
        print(f"Worker {self.worker_num}:", url)
        hotels_cards, err_tag = self.run_function_with_retry(
            func=self.get_hotel_cards,
            parm=(),
            err=(TimeoutException, ElementClickInterceptedException),
            msg='get_hotel_cards'
        )
        if err_tag:
            hotels_cards = self.driver.find_elements(
                By.XPATH, "//section[@class='results']/ol/li/div/a[@data-stid='open-hotel-information']",
            )
            if len(hotels_cards) == 0:
                with open("logs/hotels/hotels_crawler.log", "a") as e:
                    message = f'[Fail hotel url] {url}\n'
                    print(message)
                    e.write(message)
        hotels_cards = [x.get_attribute("href") for x in hotels_cards]
        print(f"worker {self.worker_num}: <<{div}>> {len(hotels_cards)} cards \n")
        hotel_ls = []
        self.remove_redundant_window()
        for c in range(len(hotels_cards)):
            _, err_tag = self.run_function_with_retry(
                func=self.fetch_data,
                parm=(hotels_cards[c], c, hotel_ls),
                err=TimeoutException,
                msg='fetch_data'
            )
            if err_tag:
                continue
        return hotel_ls

    def run(self):
        col = client["personal_project"]["hotels"]
        while not job_queue.empty():
            hotel_data = self.get_hotelcom_hotels(job_queue.get())
            col.insert_many(hotel_data, bypass_document_validation=True)


if __name__ == "__main__":
    START_TIME = datetime.datetime.now()
    print(f"hotels started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    with open("jsons/divisions.json") as f:
        divisions = json.load(f)
    job_queue = queue.Queue()
    for job_index in divisions:
        job_queue.put(job_index)

    workers = []
    worker_count = 4
    for i in range(worker_count):
        num = i + 1
        driver = webdriver.Chrome(
            ChromeDriverManager(version="104.0.5112.20").install(), options=options
        )
        driver.delete_all_cookies()
        driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
        worker.driver.quit()
        print(f"{worker.worker_num} done")

    END_TIME = datetime.datetime.now()
    print(f"hotels started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"hotels finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"hotels cost {(END_TIME-START_TIME).seconds//60} minutes")
