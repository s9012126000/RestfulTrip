from crawler_config import *
from mysql_config import *
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


def get_thirty_dates():
    date_ls = []
    for d in range(30):
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
            prices, empty = self.get_hotel_price(jb)
            if prices:
                price_to_sql(prices, self.db)
                print(f"insert {jb['hotel_id']} successfully")
            else:
                print(f"{jb['hotel_id']} is empty")
            if empty['date']:
                empty_to_sql(empty, self.db)
            print(f"hotel {jb['hotel_id']}: done")

    def get_hotel_price(self, link):
        date_ls = get_thirty_dates()
        uid = link['id']
        url = link['url']
        price_ls = []
        empty_date = []
        for date in date_ls:
            checkin = date
            checkout = date + datetime.timedelta(days=1)
            replaces = {
                'chkin=2022-10-01': f'chkin={checkin}',
                'chkout=2022-10-02': f'chkout={checkout}',
            }
            url_new = replace_all(url, replaces)
            # driver.set_page_load_timeout(10)
            try:
                self.driver.get(url_new)
                self.driver.execute_script("window.scrollTo(0, 800)")
                time.sleep(0.5)
                wait = WebDriverWait(self.driver, 1)
                cards = wait.until(ec.presence_of_element_located((By.ID, "Offers")))
                wait.until(ec.presence_of_all_elements_located((By.TAG_NAME, 'ul')))
                try:
                    empty = self.driver.find_element(By.XPATH, "//div[@data-stid='error-messages']").text
                    print(empty)
                    raise TimeoutException
                except NoSuchElementException:
                    pass
                wait.until(ec.presence_of_all_elements_located((By.XPATH, "//div[@data-stid='price-summary']")))
                room = cards.find_elements(By.TAG_NAME, 'ul')
                room = [int(re.search(r"最多可入住 (\d) 人", x.text).group(1)) for x in room]

                price = cards.find_elements(By.XPATH, "//div[@data-stid='price-summary']")
                price = [int(re.search(r"\d+", (x.text.replace(',', ''))).group())
                         for x in price]
                room = room[0:len(price)]
                price_dict = {}
                for i in range(len(room)):
                    try:
                        if price_dict[room[i]] > price[i]:
                            price_dict[room[i]] = price[i]
                    except KeyError:
                        price_dict[room[i]] = price[i]
                price_pack = [{
                    'date': date,
                    'price': price,
                    'resource_id': uid,
                    'person': person}
                    for person, price in price_dict.items()]
                pprint(price_pack)
                price_ls.extend(price_pack)
            except TimeoutException:
                print(f"{uid} is empty at {date}")
                empty_date.append(str(date))
        empty_pack = {
            'date': empty_date,
            'resource_id': uid
        }
        pprint(empty_pack)
        return price_ls, empty_pack


if __name__ == '__main__':
    MyDb = pool.get_conn()
    START_TIME = datetime.datetime.now()
    print(f"hotels started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute('SELECT id, url, hotel_id  FROM resources WHERE resource = 1 ORDER BY hotel_id')
    urls = cursor.fetchall()[0:10]
    MyDb.commit()
    pool.release(MyDb)

    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 1
    for i in range(worker_count):
        MyDb = pool.get_conn()
        num = i + 1
        driver = webdriver.Chrome(ChromeDriverManager(version='104.0.5112.20').install(), options=options)
        driver.delete_all_cookies()
        worker = Worker(num, driver, MyDb)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
        worker.driver.quit()
        pool.release(worker.db)
        print(f'{worker.worker_num} done')

    END_TIME = datetime.datetime.now()
    print(f"hotels started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"hotels finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"hotels cost {round(((END_TIME-START_TIME).seconds/60), 2)} minutes")
    os._exit(0)
