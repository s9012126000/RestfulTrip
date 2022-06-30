from config.mongo_config import *
from config.crawler_config import *
import threading
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
        print(URL)
        
        self.driver.get(URL)
        headers = driver.execute_script(
            "var req = new XMLHttpRequest();req.open('GET', document.location, false);req.send(null);return req.getAllResponseHeaders()")
        headers = headers.splitlines()
        print(headers)
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            """
        })
        last_len = 0
        while True:
            cards = self.driver.find_element(By.TAG_NAME, 'html').text
            print(cards)
            self.driver.execute_script("window.scrollTo(0, 50000)")
            time.sleep(2)
            elm = WebDriverWait(self.driver, 20).until(
                ec.element_to_be_clickable((By.XPATH, "//button[@data-stid='show-more-results']"))
            )
            print('break through')
            elm.click()
            time.sleep(1)
            check = len(self.driver.find_elements(By.XPATH, "//section[@class='results']/ol/li"))
            if check > last_len:
                last_len = check
            elif check == last_len:
                break
        cards = self.driver.find_elements(
            By.XPATH, "//section[@class='results']/ol/li/div/a[@data-stid='open-hotel-information']")
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
        print(f"{detail} success")
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return pack


if __name__ == '__main__':
    with open('jsons/divisions.json') as f:
        divisions = json.load(f)
    job_queue = queue.Queue()
    for job_index in divisions:
        job_queue.put(job_index)

    workers = []
    worker_count = 1
    for i in range(worker_count):
        num = i+1
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        driver.delete_all_cookies()
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.run()

    for worker in workers:
        worker.join()
