from config.mysql_config import *
import json
import pika

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


def fetching_hotels(resource):
    mysql_db = pool.get_conn()
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(f'SELECT id, url, hotel_id  FROM resources WHERE resource = {resource} ORDER BY hotel_id')
    urls = cursor.fetchall()
    mysql_db.commit()
    pool.release(mysql_db)
    return urls


def sending_queue(urls, que):
    channel.queue_declare(queue=que, durable=True)
    for url in urls:
        msg = json.dumps(url).encode('UTF-8')
        channel.basic_publish(exchange='',
                              routing_key=que,
                              body=msg)


if __name__ == '__main__':
    hotels = fetching_hotels(1)
    booking = fetching_hotels(2)
    agoda = fetching_hotels(3)
    sending_queue(hotels, 'hotels')
    sending_queue(booking, 'booking')
    sending_queue(agoda, 'agoda')
    conn.close()
    os._exit(0)
