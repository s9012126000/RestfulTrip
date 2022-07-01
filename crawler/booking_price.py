from config.crawler_config import *
from config.mysql_config import *
from pprint import pprint
import datetime
import threading
import queue
import time
import re


def get_thirty_dates():
    date_ls = []
    for d in range(30):
        date = (datetime.datetime.now().date() + datetime.timedelta(days=d))
        date_ls.append(date)
    return date_ls


def replace_all(text, dt):
    for i, j in dt.items():
        text = text.replace(i, j)
    return text


def get_booking_price(link):
    date_ls = get_thirty_dates()
    uid = link['id']
    url = link['url']
    price_ls = []
    for date in date_ls:
        checkin = date
        checkout = date + datetime.timedelta(days=1)
        replaces = {
            'checkin=2022-06-18': f'checkin={checkin}',
            'checkout=2022-06-19': f'checkout={checkout}',
        }
        url_new = replace_all(url, replaces)

        def fetching():
            headers['User-Agent'] = UserAgent().random
            hotel_req = requests.get(url_new, headers=headers, allow_redirects=False)
            hotel_soup = BeautifulSoup(hotel_req.text, 'html.parser')
            room = hotel_soup.find(id='hprt-table').findAll('span', attrs={"class": "bui-u-sr-only"})
            room = [x.text.replace(',', '') for x in room]
            room = ''.join(room)
            price = [x for x in re.findall(r"目前價格\nTWD\xa0\d+|房價\nTWD\xa0\d+", room)]
            price = [int(re.search(r"\xa0(\d+)", x).group(1)) for x in price]
            room_type = re.findall(r"—\d|最多人數: \d", room)
            room_type = [int(re.search(r"\d", x).group()) for x in room_type]
            price_dict = {}
            for i in range(len(room_type)):
                try:
                    if price_dict[room_type[i]] > price[i]:
                        price_dict[room_type[i]] = price[i]
                except KeyError:
                    price_dict[room_type[i]] = price[i]
            price_pack = [{
                'date': date,
                'price': price,
                'resource_id': uid,
                'person': person}
                for person, price in price_dict.items()]
            pprint(price_pack)
            price_ls.extend(price_pack)
        try:
            fetching()
        except AttributeError:
            for i in range(5):
                try:
                    print(f'attempt {i+1}')
                    time.sleep(1)
                    fetching()
                    break
                except AttributeError:
                    print(f'attempt {i+1} fail')
                    if i == 4:
                        with open('logs/booking_lost_price.txt', 'a') as e:
                            e.write(url_new + '\n')
                        print(f"lost data")
    return price_ls


class Worker(threading.Thread):
    def __init__(self, worker_num):
        threading.Thread.__init__(self)
        self.worker_num = worker_num

    def run(self):
        while not job_queue.empty():
            jb = job_queue.get()
            prices = get_booking_price(jb)
            if prices:
                dt_to_sql('price', prices)
                print(f"insert {jb['hotel_id']} successfully")
            else:
                print(f"{jb['hotel_id']} is empty")
            print(f"hotel {jb['hotel_id']}: done")


if __name__ == '__main__':
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute('SELECT id, url, hotel_id  FROM resources WHERE resource = 2 ORDER BY hotel_id')
    urls = cursor.fetchall()

    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 1
    for i in range(worker_count):
        num = i + 1
        worker = Worker(num)
        workers.append(worker)

    for worker in workers:
        worker.start()
