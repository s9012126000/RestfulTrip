from config.mysql_config import *
import datetime
import schedule
import time
import pika

mysql_db = pool.get_conn()
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


def store_start_time_dashboard():
    date = datetime.datetime.now().date()
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    start = [
        (date, 1, 2, start_time),
        (date, 2, 2, start_time),
        (date, 3, 2, start_time)
    ]
    sql = "INSERT IGNORE INTO  dash_time (date, resource, pipe, start) VALUES (%s, %s, %s, %s)"
    cursor.executemany(sql, start)
    mysql_db.commit()


def store_end_time_dashboard(res):
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(f"SELECT * FROM dash_time WHERE resource = {res} AND pipe = 2 ORDER BY date DESC")
    last_row = cursor.fetchone()
    mysql_db.commit()
    if last_row['end'] is None:
        date = last_row['date']
        end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        sql = f"UPDATE dash_time SET end = '{end_time}' WHERE date = '{date}' AND resource = {res}"
        cursor.execute(sql)
        mysql_db.commit()
        print(f"hotel {res} is done")


def store_price_dashboard(res):
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(f"""
        SELECT count(p.price) AS c
        FROM resources AS re 
        INNER JOIN price AS p on re.id = p.resource_id 
        WHERE resource = {res}
        """)
    price_count = cursor.fetchone()['c']
    mysql_db.commit()

    cursor.execute(f"SELECT * FROM dash_time WHERE resource = {res} AND pipe = 2 ORDER BY date DESC")
    date = cursor.fetchone()['date']
    mysql_db.commit()

    dash_price = (date, res, price_count)
    sql = "INSERT INTO dash_price (date, resource, price) VALUES (%s, %s, %s)"
    cursor.execute(sql, dash_price)
    mysql_db.commit()


def check_queue_size():
    conn = pika.BlockingConnection(conn_param)
    channel = conn.channel()

    hotels_que = channel.queue_declare(queue='hotels', durable=True)
    hotel_size = hotels_que.method.message_count
    if hotel_size == 0:
        store_end_time_dashboard(1)

    booking_que = channel.queue_declare(queue='booking', durable=True)
    booking_size = booking_que.method.message_count
    if booking_size == 0:
        store_end_time_dashboard(2)

    agoda_que = channel.queue_declare(queue='agoda', durable=True)
    agoda_size = agoda_que.method.message_count
    if agoda_size == 0:
        store_end_time_dashboard(3)

    if hotel_size == 0 and booking_size == 0 and agoda_size == 0:
        for i in range(3):
            store_price_dashboard(i+1)
        os._exit(0)


if __name__ == '__main__':
    schedule.every(10).seconds.do(check_queue_size)
    store_start_time_dashboard()
    while True:
        schedule.run_pending()
        time.sleep(1)