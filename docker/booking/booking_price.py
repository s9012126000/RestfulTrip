from crawler_config import *
from mysql_config import *
import datetime
import functools
import threading
import json
import pika
import re
import os


credentials = pika.credentials.PlainCredentials(
    username=os.getenv('rbt_user'),
    password=os.getenv('rbt_pwd')
)
conn_param = pika.ConnectionParameters(
    host=os.getenv('rbt_host'),
    port=5672,
    credentials=credentials,
    heartbeat=5,
    connection_attempts=5,
    locale='zh-TW'
)
conn = pika.BlockingConnection(conn_param)
channel = conn.channel()
channel.exchange_declare(exchange="test_exchange", exchange_type="direct", passive=False, durable=True, auto_delete=False)
channel.queue_declare(queue="booking", durable=True)
channel.queue_bind(queue="booking", exchange="test_exchange", routing_key="que")
channel.basic_qos(prefetch_count=1)


def replace_all(text, dt):
    for i, j in dt.items():
        text = text.replace(i, j)
    return text


def get_dates():
    date_ls = []
    for d in range(30):
        date = (datetime.datetime.now().date() + datetime.timedelta(days=d))
        date_ls.append(date)
    return date_ls


def ack_message(channel, delivery_tag):
    if channel.is_open:
        channel.basic_ack(delivery_tag)


def get_booking_price(link):
    date_ls = get_dates()
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
            price_ls.extend(price_pack)
        try:
            fetching()
            print(f'receive {uid} price at {date}')
        except AttributeError:
            try:
                fetching()
                print(f'receive {uid} price at {date}')
            except AttributeError:
                print(f"{uid} is empty at {date}")
    return price_ls


def do_work(connection, channel, delivery_tag, body):
    db = pool.get_conn()
    db.ping(reconnect=True)
    url = json.loads(body.decode('UTF-8'))
    prices = get_booking_price(url)
    if prices:
        price_to_sql(prices, db)
        print(f"insert {url['hotel_id']} successfully")
    else:
        print(f"{url['hotel_id']} is empty")
    print(f"hotel {url['hotel_id']}: done")

    cb = functools.partial(ack_message, channel, delivery_tag)
    connection.add_callback_threadsafe(cb)
    pool.release(db)


def on_message(channel, method_frame, header_frame, body, args):
    (connection, threads) = args
    delivery_tag = method_frame.delivery_tag
    t = threading.Thread(target=do_work, args=(connection, channel, delivery_tag, body))
    t.start()
    threads.append(t)


if __name__ == '__main__':
    threads = []
    on_message_callback = functools.partial(on_message, args=(conn, threads))
    channel.basic_consume(queue='booking',
                          auto_ack=False,
                          on_message_callback=on_message_callback)
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    for thread in threads:
        thread.join()


    conn.close()