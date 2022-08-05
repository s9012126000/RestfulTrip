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

    def scroll_to_bottom(self):
        for _i in range(4):
            time.sleep(1)
            try:
                self.driver.execute_script("window.scrollTo(0, 50000)")
            except WebDriverException:
                pass
            time.sleep(1)

    def run_function_with_retry(self, func, parm, err, msg):
        result = None
        tag = False
        try:
            result = func(*parm)
        except err:
            for i in range(5):
                try:
                    self.driver.refresh()
                    result = func(*parm)
                    break
                except err:
                    print(f"[{datetime.datetime.now().isoformat()}] worker {self.worker_num}, attempt {i+1} {msg} fail")
                    if i == 4:
                        with open("logs/hotels/agoda_crawler.log", "a") as e:
                            message = f'[{datetime.datetime.now().isoformat()}][{err.__name__}] {msg} fail\n'
                            print(message)
                            e.write(message)
                        tag = True
        return result, tag

    def get_region_pages(self, div):
        url = "https://www.agoda.com/zh-tw/"
        self.driver.get(url)
        time.sleep(1)
        wait = WebDriverWait(self.driver, 10)
        wait.until(ec.element_to_be_clickable((By.XPATH, "//input[@data-selenium='textInput']"))).click()
        self.driver.find_element(
            By.XPATH, "//input[@data-selenium='textInput']"
        ).send_keys(div)
        wait.until(ec.element_to_be_clickable((By.XPATH, "//li[@data-selenium='autosuggest-item']"))).click()
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//li[@data-selenium='allRoomsTab']").click()
        time.sleep(1)
        print(f"worker {self.worker_num}: form filled")
        self.driver.find_element(By.XPATH, "//button[@data-selenium='searchButton']").click()
        try:
            wait.until(ec.element_to_be_clickable(
                (By.XPATH, "//button[@data-element-name='asq-ssr-popup-no-button']"))
            ).click()
        except TimeoutException:
            pass

    def get_hotel_cards(self, div):
        cards = []
        while True:
            try:
                self.scroll_to_bottom()
                card = WebDriverWait(self.driver, 10).until(
                    ec.presence_of_all_elements_located((By.XPATH, "//a[@class='PropertyCard__Link']"))
                )
                card = [
                    x.get_attribute("href")
                    for x in card
                    if x.get_attribute("href") is not None
                ]
                cards.extend(card)
            except StaleElementReferenceException:
                break
            try:
                self.driver.find_element(By.ID, "paginationNext").click()
            except NoSuchElementException:
                break
        print(f"worker {self.worker_num}: <<{div}>> get {len(cards)} cards")
        return cards

    def fetch_data(self, hotel_ls):
        wait = WebDriverWait(self.driver, 5)
        try:
            name = wait.until(
                ec.presence_of_element_located((By.XPATH, "//h1[@data-selenium='hotel-header-name']"))
            ).text
        except TimeoutException:
            raise StaleElementReferenceException
        address = wait.until(
            ec.presence_of_element_located((By.XPATH, "//span[@data-selenium='hotel-address-map']"))
        ).text
        link = self.driver.current_url
        try:
            rating = wait.until(
                ec.presence_of_element_located((By.XPATH, "//div[@class='ReviewScoreCompact__section']"))
            ).text
        except TimeoutException:
            rating = "No enough record"
        try:
            img = wait.until(
                    ec.presence_of_element_located((By.XPATH, "//div[@data-component='PropertyMosaic']"))
                ).find_element(By.TAG_NAME, "img").get_attribute("src")
            print(img)
        except (TimeoutException, NoSuchElementException):
            img = "non-provided"
        try:
            des = wait.until(
                ec.presence_of_element_located((By.XPATH, "//div[@data-element-name='property-short-description']"))
            ).text
        except TimeoutException:
            des = "non-provided"
        try:
            star = wait.until(
                ec.presence_of_element_located((By.XPATH, "//i[@data-selenium='mosaic-hotel-rating']"))
            ).get_attribute("class")
        except TimeoutException:
            star = "non-provided"
        pack = {
            "name": name,
            "url": link,
            "address": address,
            "rating": rating,
            "img": img,
            "des": des,
            "star": star,
        }
        if any(val == "" for val in pack.values()):
            raise StaleElementReferenceException
        hotel_ls.append(pack)

    def get_hotel_data(self, div):
        cards = self.get_hotel_cards(div)
        hotel_ls = []
        for c in range(len(cards)):
            self.driver.get(cards[c])
            self.run_function_with_retry(
                func=self.fetch_data,
                parm=(hotel_ls,),
                err=StaleElementReferenceException,
                msg='fetch_data'
            )
            print(f"worker {self.worker_num}: {c} {hotel_ls[-1]['name']} success")
        return hotel_ls

    def run(self):
        col = client["personal_project"]["agoda"]
        while not job_queue.empty():
            region = job_queue.get()
            self.run_function_with_retry(
                func=self.get_region_pages,
                parm=(region, ),
                err=ElementClickInterceptedException,
                msg='get_region_pages'
            )
            hotel_data = self.get_hotel_data(region)
            col.insert_many(hotel_data)
            print(f"store successfully at {time.perf_counter()}")


if __name__ == "__main__":
    START_TIME = datetime.datetime.now()
    print(f"agoda started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    with open("jsons/divisions.json") as d:
        divisions = json.load(d)
    ext = ["花蓮市", "台東市", "宜蘭市", "台南縣", "墾丁"]
    divisions.extend(ext)
    job_queue = queue.Queue()
    for job_index in divisions:
        job_queue.put(job_index)
    workers = []
    worker_count = 4
    for i in range(worker_count):
        num = i + 1
        driver = webdriver.Chrome(ChromeDriverManager(version="104.0.5112.20").install(), options=options)
        driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        driver.delete_all_cookies()
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
        worker.driver.quit()
        print(f"{worker.worker_num} done")

    END_TIME = datetime.datetime.now()
    print(f"agoda started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"agoda finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"agoda cost {(END_TIME-START_TIME).seconds//60} minutes")
