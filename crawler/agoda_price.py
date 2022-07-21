from config.crawler_config import *
from config.mysql_config import *
from pprint import pprint
import datetime
import threading
import queue
import time
import re


def replace_all(text, dt):
    for i, j in dt.items():
        text = text.replace(i, j)
    return text


def get_dates():
    date_ls = []
    for d in range(14):
        date = (datetime.datetime.now().date() + datetime.timedelta(days=d))
        date_ls.append(date)
    return date_ls


class Worker(threading.Thread):
    def __init__(self, worker_num, driver, db):
        threading.Thread.__init__(self)
        self.worker_num = worker_num
        self.driver = driver
        self.db = db

    def run(self):
        while not job_queue.empty():
            jb = job_queue.get()
            prices, empty = self.get_agoda_price(jb)
            if prices:
                price_to_sql(prices, self.db)
                print(f"insert {jb['hotel_id']} successfully")
            else:
                print(f"{jb['hotel_id']} is empty")
            if empty['date']:
                empty_to_sql(empty, self.db)
            print(f"hotel {jb['hotel_id']}: done")

    def get_agoda_price(self, link):
        date_ls = get_dates()
        uid = link['id']
        url = link['url']
        price_ls = []
        empty_date = []
        for date in date_ls:
            replaces = {'checkIn=2022-06-28': f'checkIn={date}'}
            url_new = replace_all(url, replaces)
    
            def fetching():
                self.driver.get(url_new)
                time.sleep(0.5)
                wait = WebDriverWait(self.driver, 1)
                price = wait.until(
                    ec.presence_of_all_elements_located((By.XPATH, "//strong[@data-ppapi='room-price']"))
                )
                price = [int(x.text.replace(',', '')) for x in price]
                if 0 in price:
                    self.driver.refresh()
                    time.sleep(1)
                    price = wait.until(
                        ec.presence_of_all_elements_located((By.XPATH, "//strong[@data-ppapi='room-price']"))
                    )
                    price = [int(x.text.replace(',', '')) for x in price]
                room = wait.until(
                    ec.presence_of_all_elements_located((By.XPATH, "//div[@data-ppapi='max-occupancy']"))
                )
                room = [x.get_attribute('innerHTML') for x in room]
                room_ls = []
                for r in room:
                    try:
                        room_ls.append(re.search(r"occupancy\">(\d)</span>", r).group(1))
                    except AttributeError:
                        room_ls.append(len(re.findall(r"adult", r)))
                price_dict = {}
                for i in range(len(room_ls)):
                    try:
                        if price_dict[room_ls[i]] > price[i]:
                            price_dict[room_ls[i]] = price[i]
                    except KeyError:
                        price_dict[room_ls[i]] = price[i]
                price_pack = [{
                    'date': date,
                    'price': price,
                    'resource_id': uid,
                    'person': person}
                    for person, price in price_dict.items()]
                price_ls.extend(price_pack)
                pprint(price_pack)
            try:
                fetching()
            except TimeoutException:
                print(f"{uid} is empty at {date}")
                empty_date.append(str(date))
            except StaleElementReferenceException:
                print(f"{uid} is empty at {date}")
                empty_date.append(str(date))

        empty_pack = {
            'date': empty_date,
            'resource_id': uid
        }
        pprint(empty_pack)
        return price_ls, empty_pack
                        
                        
if __name__ == '__main__':
    mysql_db = pool.get_conn()
    START_TIME = datetime.datetime.now()
    print(f"agoda started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute('SELECT id, url, hotel_id  FROM resources WHERE resource = 3 ORDER BY hotel_id')
    urls = cursor.fetchall()
    mysql_db.commit()
    pool.release(mysql_db)

    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 4
    for i in range(worker_count):
        mysql_db = pool.get_conn()
        num = i + 1
        driver = webdriver.Chrome(ChromeDriverManager(version='104.0.5112.20').install(), options=options)
        driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
        driver.delete_all_cookies()
        worker = Worker(num, driver, mysql_db)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
        worker.driver.quit()
        pool.release(worker.db)
        print(f'{worker.worker_num} done')

    END_TIME = datetime.datetime.now()
    print(f"agoda started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"agoda finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"agoda cost {round(((END_TIME-START_TIME).seconds/60), 2)} minutes")
    os._exit(0)
