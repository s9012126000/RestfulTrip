from personal_project.config.crawler_config import *
from personal_project.config.mysql_config import *
from pprint import pprint
import datetime
import threading
import queue
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
    def __init__(self, worker_num, driver):
        threading.Thread.__init__(self)
        self.worker_num = worker_num
        self.driver = driver

    def run(self):
        while not job_queue.empty():
            jb = job_queue.get()
            prices = self.get_hotel_price(jb)
            if prices:
                dt_to_sql('price', prices)
                print(f"insert {jb['hotel_id']} successfully")
            else:
                print(f"{jb['hotel_id']} is empty")
            print(f"hotel {jb['hotel_id']}: done")

    def get_hotel_price(self, link):
        date_ls = get_thirty_dates()
        uid = link['id']
        url = link['url']
        price_ls = []
        for date in date_ls:
            checkin = date
            checkout = date + datetime.timedelta(days=1)
            replaces = {
                'chkin=2022-10-01': f'chkin={checkin}',
                'chkout=2022-10-02': f'chkout={checkout}',
            }
            url_new = replace_all(url, replaces)
            self.driver.get(url_new)
            self.driver.execute_script("window.scrollTo(0, 800)")
            wait = WebDriverWait(self.driver, 3)
            try:
                cards = wait.until(ec.presence_of_element_located((By.ID, "Offers")))
                wait.until(ec.presence_of_all_elements_located((By.TAG_NAME, 'ul')))
                wait.until(ec.presence_of_all_elements_located((By.XPATH, "//div[@data-stid='price-summary']")))
                # room = cards.find_elements(By.CLASS_NAME, "uitk-heading-6")
                # room = [x.text for x in room]
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
                continue
        return price_ls


if __name__ == '__main__':
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute('SELECT id, url, hotel_id  FROM resources WHERE resource = 1 and hotel_id > 490')
    urls = cursor.fetchall()

    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 3
    for i in range(worker_count):
        num = i + 1
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        driver.delete_all_cookies()
        worker = Worker(num, driver)
        workers.append(worker)

    for worker in workers:
        worker.start()