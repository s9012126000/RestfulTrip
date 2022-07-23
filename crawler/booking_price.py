from config.crawler_config import *
from config.mysql_config import *
from pprint import pprint
import datetime
import threading
import queue
import re


def get_dates():
    date_ls = []
    for d in range(14):
        date = datetime.datetime.now().date() + datetime.timedelta(days=d)
        date_ls.append(date)
    return date_ls


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


class Worker(threading.Thread):
    def __init__(self, worker_num, db):
        threading.Thread.__init__(self)
        self.worker_num = worker_num
        self.db = db

    def run(self):
        while not job_queue.empty():
            jb = job_queue.get()
            prices, empty = self.get_booking_price(jb)
            if prices:
                price_to_sql(prices, self.db)
                print(f"insert {jb['hotel_id']} successfully")
            else:
                print(f"{jb['hotel_id']} is empty")
            if empty["date"]:
                empty_to_sql(empty, self.db)
            print(f"hotel {jb['hotel_id']}: done")

    def get_booking_price(self, link):
        date_ls = get_dates()
        uid = link["id"]
        url = link["url"]
        price_ls = []
        empty_date = []
        for date in date_ls:
            checkin = date
            checkout = date + datetime.timedelta(days=1)
            replaces = {
                "checkin=2022-06-18": f"checkin={checkin}",
                "checkout=2022-06-19": f"checkout={checkout}",
            }
            url_new = replace_all(url, replaces)

            def fetching():
                headers["User-Agent"] = UserAgent().random
                hotel_req = requests.get(
                    url_new, headers=headers, allow_redirects=False
                )
                hotel_soup = BeautifulSoup(hotel_req.text, "html.parser")
                room = hotel_soup.find(id="hprt-table").findAll(
                    "span", attrs={"class": "bui-u-sr-only"}
                )
                room = [x.text.replace(",", "") for x in room]
                room = "".join(room)
                price = [
                    x for x in re.findall(r"目前價格\nTWD\xa0\d+|房價\nTWD\xa0\d+", room)
                ]
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
                price_pack = [
                    {"date": date, "price": price, "resource_id": uid, "person": person}
                    for person, price in price_dict.items()
                ]
                pprint(price_pack)
                price_ls.extend(price_pack)

            try:
                fetching()
            except AttributeError:
                try:
                    print(f"{self.worker_num} attempt {uid}")
                    fetching()
                except AttributeError:
                    print(f"{uid} is empty at {date}")
                    empty_date.append(str(date))
        empty_pack = {"date": empty_date, "resource_id": uid}
        pprint(empty_pack)
        return price_ls, empty_pack


if __name__ == "__main__":
    mysql_db = pool.get_conn()
    START_TIME = datetime.datetime.now()
    print(f"booking started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(
        "SELECT id, url, hotel_id  FROM resources WHERE resource = 2 ORDER BY hotel_id"
    )
    urls = cursor.fetchall()
    mysql_db.commit()
    pool.release(mysql_db)

    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 20
    for i in range(worker_count):
        mysql_db = pool.get_conn()
        num = i + 1
        worker = Worker(num, mysql_db)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()
        pool.release(worker.db)
        print(f"{worker.worker_num} done")

    END_TIME = datetime.datetime.now()
    print(f"booking started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"booking finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"booking cost {round(((END_TIME - START_TIME).seconds / 60), 2)} minutes")
    os._exit(0)
