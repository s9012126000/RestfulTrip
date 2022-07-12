from mysql_config import *
import json
import pika

credentials = pika.credentials.PlainCredentials(
    username=os.getenv('rbt_user'),
    password=os.getenv('rbt_pwd')
)

conn_param = pika.ConnectionParameters(
    host=os.getenv('rbt_host'),
    port=5672,
    credentials=credentials
)

conn = pika.BlockingConnection(conn_param)
channel = conn.channel()


def fetching_hotels(resource):
    MyDb = pool.get_conn()
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute(f'SELECT id, url, hotel_id  FROM resources WHERE resource = {resource} ORDER BY hotel_id')
    urls = cursor.fetchall()[0:10]
    MyDb.commit()
    pool.release(MyDb)
    return urls


def sending_queue(urls, que):
    channel.queue_declare(queue=que)
    for url in urls:
        msg = json.dumps(url).encode('UTF-8')
        channel.basic_publish(exchange='',
                              routing_key=que,
                              body=msg)
    conn.close()


if __name__ == '__main__':
    hotels = fetching_hotels(1)
    # booking = fetching_hotels(2)
    # agoda = fetching_hotels(3)
    sending_queue(hotels, 'hotels')
    # sending_queue(booking, 'booking')
    # sending_queue(agoda, 'agoda')
    os._exit(0)
