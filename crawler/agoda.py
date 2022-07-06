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
            region = job_queue.get()
            try:
                self.get_region_hotels(region)
            except ElementClickInterceptedException:
                for i in range(5):
                    try:
                        self.driver.refresh()
                        print(f'form filled attempt {i}')
                        self.get_region_hotels(region)
                        break
                    except ElementClickInterceptedException:
                        print(f'attempt {i} fail')
                        if i == 4:
                            with open('logs/hotels/agoda_lost_region.log', 'a') as e:
                                e.write(region, '\n')
                            print(f"lost region")
            self.get_hotels()
            
    def get_region_hotels(self, div):
        url = 'https://www.agoda.com/zh-tw/'
        self.driver.get(url)
        time.sleep(1)
        WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.XPATH, "//input[@data-selenium='textInput']"))
        ).click()
        self.driver.find_element(By.XPATH, "//input[@data-selenium='textInput']").send_keys(div)
        WebDriverWait(self.driver, 10).until(
            ec.element_to_be_clickable((By.XPATH, "//li[@data-selenium='autosuggest-item']"))
        ).click()
        time.sleep(1)
        self.driver.find_element(By.XPATH, "//li[@data-selenium='allRoomsTab']").click()
        time.sleep(1)
        print(f'form {self.worker_num} filled')
        self.driver.find_element(By.XPATH, "//button[@data-selenium='searchButton']").click()
        try:
            WebDriverWait(self.driver, 10).until(
                ec.element_to_be_clickable((By.XPATH, "//button[@data-element-name='asq-ssr-popup-no-button']"))
            ).click()
        except TimeoutException:
            pass

    def get_hotels(self):
        col = client['personal_project']['agoda']
        while True:
            def get_cards():
                self.scroll_to_bottom()
                card = WebDriverWait(self.driver, 10).until(
                    ec.presence_of_all_elements_located((By.XPATH, "//a[@class='PropertyCard__Link']"))
                )
                card = [x.get_attribute('href') for x in card if x.get_attribute('href') is not None]
                print(f'hotel cards per page: {len(card)}')
                return card
            try:
                cards = get_cards()
            except StaleElementReferenceException:
                tag = False
                cards = ''
                for i in range(5):
                    try:
                        print(f'get card attempt {i}')
                        self.driver.refresh()
                        time.sleep(1)
                        cards = get_cards()
                        break
                    except StaleElementReferenceException:
                        print(f'get card attempt {i} fail')
                        if i == 4:
                            tag = True
                            with open('logs/hotels/agoda_lost_cards.log', 'a') as e:
                                e.write(self.driver.current_url, '\n')
                            print(f"lost cards")
                if tag:
                    break
            except TimeoutException:
                print('end of this pages')
                break            
            hotel_ls = []
            for c in cards:
                def open_window():
                    self.driver.execute_script("window.open()")
                    WebDriverWait(self.driver, 10).until(ec.number_of_windows_to_be(2))
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    self.driver.get(c)
                    time.sleep(1)
                try:
                    open_window()
                except TimeoutException:
                    for k in range(5):
                        try:
                            print(f'open card attempt {k}')
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                            open_window()
                        except TimeoutException:
                            print(f'open card attempt {k} fail')

                def fetching():
                    wait = WebDriverWait(self.driver, 5)
                    name = wait.until(
                        ec.presence_of_element_located((By.XPATH, "//h1[@data-selenium='hotel-header-name']"))
                    ).text
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
                            ec.presence_of_element_located((By.ID, 'PropertyMosaic'))
                        ).find_element(By.TAG_NAME, 'img').get_attribute('src')
                    except TimeoutException:
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
                        ).get_attribute('class')
                    except TimeoutException:
                        star = "non-provided"
                    pack = {
                        'name': name,
                        'url': link,
                        'address': address,
                        'rating': rating,
                        'img': img,
                        'des': des,
                        'star': star
                    }
                    if any(val == '' for val in pack.values()):
                        raise StaleElementReferenceException
                    hotel_ls.append(pack)
                    print(f'{name}: success')
                try:
                    fetching()
                except StaleElementReferenceException:
                    for j in range(5):
                        try:
                            time.sleep(3)
                            print(f'fetching attempt {j}')
                            fetching()
                            break
                        except StaleElementReferenceException:
                            print(f'attempt {j} fail')
                            if j == 4:
                                with open('logs/hotels/agoda_lost_data.log', 'a') as e:
                                    lnk = self.driver.current_url
                                    e.write(lnk, '\n')
                                print(f"lost data")
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
            col.insert_many(hotel_ls)
            print(f'store successfully at {time.perf_counter()}')
            try:
                self.scroll_to_bottom()
                self.driver.find_element(By.ID, 'paginationNext').click()
            except NoSuchElementException:
                break

    def scroll_to_bottom(self):
        for _i in range(4):
            time.sleep(1)
            try:
                self.driver.execute_script("window.scrollTo(0, 50000)")
            except WebDriverException:
                pass
            time.sleep(1)


if __name__ == '__main__':
    START_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"agoda started at {START_TIME}")
    with open('jsons/divisions.json') as d:
        divisions = json.load(d)
    ext = ['花蓮市', '台東市', '宜蘭市', '台南縣', '墾丁']
    divisions.extend(ext)
    job_queue = queue.Queue()
    for job_index in divisions:
        job_queue.put(job_index)
    workers = []
    worker_count = 3 
    for i in range(worker_count):
        num = i+1
        driver = webdriver.Chrome(ChromeDriverManager(version='104.0.5112.20').install(), options=options)
        driver.delete_all_cookies()
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()
        worker.driver.quit()
        print(f'{worker.worker_num} done')

    END_TIME = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"agoda started at {START_TIME}")
    print(f"agoda finished at {END_TIME}")
