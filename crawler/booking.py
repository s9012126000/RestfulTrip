from config.mongo_config import *
from config.crawler_config import *
from math import ceil
import threading
import datetime
import random
import json
import time
import queue


def get_region_url(path):
    with open(f"{path}/crawler/jsons/divisions.json") as d:
        divisions = json.load(d)
    ext = ["花蓮市", "台東市", "宜蘭市", "台南縣"]
    divisions.extend(ext)
    links = []
    driver = webdriver.Chrome(
        ChromeDriverManager(version="104.0.5112.20").install(), options=options
    )
    for div in divisions:
        if "臺" in div:
            div = div.replace("臺", "台")
        print(div)
        wait = WebDriverWait(driver, 10)
        driver.get("https://www.booking.com/searchresults.zh-tw.html")
        input_elm = wait.until(
            ec.visibility_of_element_located((By.XPATH, "//input[@name='ss']"))
        )
        input_elm.send_keys(div)
        driver.find_element(
            By.XPATH, "//div[@data-component='arp-searchbox']/div/div/form/div/div[6]"
        ).click()
        hotel_num = int(
            wait.until(
                ec.visibility_of_element_located((By.XPATH, "//div[@data-component='arp-header']/div/div/div/h1"))
            ).text.split(" ")[1])
        url = driver.current_url
        links.append((url, hotel_num))
    driver.quit()
    with open(f"{path}/crawler/jsons/booking_regions_urls.json", "w") as f:
        json.dump(links, f)


def get_hotel_num(div):
    headers["User-Agent"] = UserAgent().random
    req = requests.get(div, headers=headers, allow_redirects=False)
    soup = BeautifulSoup(req.text, "html.parser")
    number = int(soup.find("h1").text.replace(",", "").split(" ")[1])
    return number


def get_hotel_cards(url, offset):
    headers["User-Agent"] = UserAgent().random
    page_url = url + f"&offset={offset}"
    url_req = requests.get(page_url, headers=headers, allow_redirects=False)
    url_soup = BeautifulSoup(url_req.text, "html.parser")
    cards = url_soup.find(id="search_results_table").findAll(
        "div", attrs={"data-testid": "property-card"}
    )
    time.sleep(1)
    return cards


class Worker(threading.Thread):
    def __init__(self, worker_num):
        threading.Thread.__init__(self)
        self.worker_num = worker_num

    def run_function_with_retry(self, func, parm, err, msg):
        result = None
        tag = False
        try:
            result = func(*parm)
        except err:
            for i in range(5):
                try:
                    time.sleep(2)
                    result = func(*parm)
                    break
                except err:
                    print(
                        f"[{datetime.datetime.now().isoformat()}] worker {self.worker_num}, attempt {i + 1} {msg} fail")
                    if i == 4:
                        with open("logs/hotels/booking_crawler.log", "a") as e:
                            message = f'[{datetime.datetime.now().isoformat()}][{err.__name__}]: {msg} fail\n'
                            print(message)
                            e.write(message)
                        tag = True
        return result, tag

    def fetch_data(self, property_card, card, hotel_ls):
        link = property_card[card].find("a")["href"]
        headers["User-Agent"] = UserAgent().random
        hotel_req = requests.get(
            link, headers=headers, allow_redirects=False
        )
        hotel_soup = BeautifulSoup(hotel_req.text, "html.parser")
        name = hotel_soup.find(id="hp_hotel_name").text.strip("\n")
        address = hotel_soup.find(id="showMap2").findAll("span")[1].text
        try:
            rating = hotel_soup.find("div", attrs={"data-testid": "review-score-right-component"}).text
        except AttributeError:
            rating = "No enough record"
        img = hotel_soup.find(
            "a", attrs={"data-preview-image-layout": "main"}
        ).find("img")["src"]
        des = hotel_soup.find(id="property_description_content").text
        try:
            star = len(hotel_soup.find("span", attrs={"data-testid": "rating-stars"}).findAll("span"))
        except AttributeError:
            star = 0
        pack = {
            "name": name,
            "url": link,
            "address": address,
            "rating": rating,
            "img": img,
            "des": des,
            "star": star,
        }
        n = name.split("\n")[-1]
        print(f"worker {self.worker_num}: {card+1} {n}")
        hotel_ls.append(pack)
        time.sleep(random.randint(1, 2))

    def get_booking_hotels(self, region):
        url = region[0]
        hotel_num, err_tag = self.run_function_with_retry(
            func=get_hotel_num,
            parm=(url,),
            err=AttributeError,
            msg='get_hotel_num'
        )
        if err_tag:
            hotel_num = 1000
        iter_count = ceil(hotel_num / 25)
        offset = 0
        hotel_ls = []
        for count in range(iter_count):
            property_card, err_tag = self.run_function_with_retry(
                func=get_hotel_cards,
                parm=(url, count),
                err=AttributeError,
                msg='get_hotel_cards'
            )
            if err_tag:
                property_card = ""
                with open("logs/hotels/booking_crawler.log", "a") as e:
                    url = url + f"&offset={offset}"
                    message = f'[Fail page url] {url}\n'
                    print(message)
                    e.write(message)
            for card in range(len(property_card)):
                _, err_tag = self.run_function_with_retry(
                    func=self.fetch_data,
                    parm=(property_card, card, hotel_ls),
                    err=(AttributeError, ConnectionError),
                    msg='fetch_data'
                )
                if err_tag:
                    with open("logs/hotels/booking_crawler.log", "a") as e:
                        url = property_card[card].find("a")["href"]
                        message = f'[Fail hotel url] {url}\n'
                        print(message)
                        e.write(message)
            offset += 25
            time.sleep(random.randint(1, 3))
        print(f"store successfully: {len(hotel_ls)}")
        return hotel_ls

    def run(self):
        col = client["personal_project"]["booking"]
        while not job_queue.empty():
            hotel_data = self.get_booking_hotels(job_queue.get())
            col.insert_many(hotel_data, bypass_document_validation=True)


if __name__ == "__main__":
    START_TIME = datetime.datetime.now()
    print(f"booking started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")

    with open("jsons/booking_regions_urls.json", "r") as u:
        urls = json.load(u)
    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 13
    for i in range(worker_count):
        num = i + 1
        worker = Worker(num)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    END_TIME = datetime.datetime.now()
    print(f"booking started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"booking finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"booking cost {(END_TIME - START_TIME).seconds // 60} minutes")
