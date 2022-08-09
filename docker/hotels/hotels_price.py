from crawler_config import *
from mysql_config import *
import datetime
import functools
import threading
import json
import time
import pika
import re
import os

credentials = pika.credentials.PlainCredentials(
    username=os.getenv("rbt_user"), password=os.getenv("rbt_pwd")
)
conn_param = pika.ConnectionParameters(
    host=os.getenv("rbt_host"),
    port=5672,
    credentials=credentials,
    heartbeat=5,
    connection_attempts=5,
    locale="zh-TW",
)
conn = pika.BlockingConnection(conn_param)
channel = conn.channel()
channel.exchange_declare(
    exchange="hotel",
    exchange_type="direct",
    passive=False,
    durable=True,
    auto_delete=False,
)
channel.queue_bind(queue="hotels", exchange="hotel", routing_key="hotels")
channel.basic_qos(prefetch_count=4)


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


def get_dates():
    date_ls = []
    for d in range(2):
        date = datetime.datetime.now().date() + datetime.timedelta(days=d)
        date_ls.append(date)
    return date_ls


def fetch_data(driver, url, price_ls, date, uid):
    driver.get(url)
    driver.execute_script("window.scrollTo(0, 800)")
    time.sleep(0.5)
    wait = WebDriverWait(driver, 1)
    cards = wait.until(ec.presence_of_element_located((By.ID, "Offers")))
    wait.until(ec.presence_of_all_elements_located((By.TAG_NAME, "ul")))
    try:
        empty = driver.find_element(By.XPATH, "//div[@data-stid='error-messages']").text
        print(empty)
        raise TimeoutException
    except NoSuchElementException:
        pass
    wait.until(
        ec.presence_of_all_elements_located((By.XPATH, "//div[@data-stid='price-summary']"))
    )
    room = cards.find_elements(By.TAG_NAME, "ul")
    room = [int(re.search(r"最多可入住 (\d+) 人", x.text).group(1)) for x in room]
    price = cards.find_elements(By.XPATH, "//div[@data-stid='price-summary']")
    price = [int(re.search(r"\d+", (x.text.replace(",", ""))).group()) for x in price]
    room = room[0: len(price)]
    price_dict = {}
    for i in range(len(room)):
        try:
            if price_dict[room[i]] > price[i]:
                price_dict[room[i]] = price[i]
        except KeyError:
            price_dict[room[i]] = price[i]
    price_pack = [
        {"date": date, "price": price, "resource_id": uid, "person": person}
        for person, price in price_dict.items()
    ]
    price_ls.extend(price_pack)


def get_hotel_price(link, driver):
    date_ls = get_dates()
    resource_id = link["id"]
    hotel_id = link["hotel_id"]
    url = link["url"]
    price_ls = []
    for date in date_ls:
        driver.delete_all_cookies()
        checkin = date
        checkout = date + datetime.timedelta(days=1)
        replaces = {
            "chkin=2022-10-01": f"chkin={checkin}",
            "chkout=2022-10-02": f"chkout={checkout}",
        }
        url_new = replace_all(url, replaces)
        try:
            fetch_data(driver, url_new, price_ls, date, resource_id)
            print(f"receive {hotel_id} price at {date}")
        except TimeoutException:
            print(f"{hotel_id} is empty at {date}")
    return price_ls


def ack_message(channel, delivery_tag):
    if channel.is_open:
        channel.basic_ack(delivery_tag)


def do_work(connection, channel, delivery_tag, body, driver):
    mysql_db = pool.get_conn()
    mysql_db.ping(reconnect=True)
    url = json.loads(body.decode("UTF-8"))
    prices = get_hotel_price(url, driver)
    if prices:
        price_to_sql(prices, mysql_db)
        print(f"insert {url['hotel_id']} successfully")
    else:
        print(f"{url['hotel_id']} is empty")
    print(f"hotel {url['hotel_id']}: done")
    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)
    driver.quit()
    pool.release(mysql_db)


def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads) = args
    delivery_tag = method_frame.delivery_tag
    driver = webdriver.Chrome(
        ChromeDriverManager(version="104.0.5112.20").install(), options=options
    )
    driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": True})
    t = threading.Thread(
        target=do_work, args=(connection, channel, delivery_tag, body, driver)
    )
    t.start()
    threads.append(t)


if __name__ == "__main__":
    threads = []
    on_message_callback = functools.partial(on_message, args=(conn, threads))
    channel.basic_consume(
        queue="hotels", auto_ack=False, on_message_callback=on_message_callback
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    for thread in threads:
        thread.join()

    conn.close()
