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
    exchange="test_exchange",
    exchange_type="direct",
    passive=False,
    durable=True,
    auto_delete=False,
)
channel.queue_declare(queue="agoda", durable=True)
channel.queue_bind(queue="agoda", exchange="test_exchange", routing_key="que")
channel.basic_qos(prefetch_count=4)


def replace_all(text, dic):
    for i, j in dic.items():
        text = text.replace(i, j)
    return text


def get_dates():
    date_ls = []
    for d in range(14):
        date = datetime.datetime.now().date() + datetime.timedelta(days=d)
        date_ls.append(date)
    return date_ls


def ack_message(channel, delivery_tag):
    if channel.is_open:
        channel.basic_ack(delivery_tag)


def get_agoda_price(link, driver):
    date_ls = get_dates()
    uid = link["id"]
    url = link["url"]
    price_ls = []
    for date in date_ls:
        replaces = {"checkIn=2022-06-28": f"checkIn={date}"}
        url_new = replace_all(url, replaces)

        def fetching():
            driver.get(url_new)
            time.sleep(0.5)
            wait = WebDriverWait(driver, 1)
            price = wait.until(
                ec.presence_of_all_elements_located(
                    (By.XPATH, "//strong[@data-ppapi='room-price']")
                )
            )
            price = [int(x.text.replace(",", "")) for x in price]
            if 0 in price:
                driver.refresh()
                time.sleep(1)
                price = wait.until(
                    ec.presence_of_all_elements_located(
                        (By.XPATH, "//strong[@data-ppapi='room-price']")
                    )
                )
                price = [int(x.text.replace(",", "")) for x in price]
            room = wait.until(
                ec.presence_of_all_elements_located(
                    (By.XPATH, "//div[@data-ppapi='max-occupancy']")
                )
            )
            room = [x.get_attribute("innerHTML") for x in room]
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
            price_pack = [
                {"date": date, "price": price, "resource_id": uid, "person": person}
                for person, price in price_dict.items()
            ]
            price_ls.extend(price_pack)

        try:
            fetching()
            print(f"receive {uid} price at {date}")
        except TimeoutException:
            print(f"{uid} is empty at {date}")
        except StaleElementReferenceException:
            print(f"{uid} is empty at {date}")
    return price_ls


def do_work(connection, channel, delivery_tag, body, driver):
    mysql_db = pool.get_conn()
    mysql_db.ping(reconnect=True)
    url = json.loads(body.decode("UTF-8"))
    prices = get_agoda_price(url, driver)
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
        queue="agoda", auto_ack=False, on_message_callback=on_message_callback
    )
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    for thread in threads:
        thread.join()

    conn.close()
