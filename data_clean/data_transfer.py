from config.mongo_config import *
from config.mysql_config import *
import datetime
import boto3
import json
import os
s3 = boto3.client(
    's3',
    region_name='ap-northeast-1',
    aws_access_key_id=os.getenv('AWS_keyid'),
    aws_secret_access_key=os.getenv('AWS_key')
)
S3 = boto3.resource('s3')


def pack_data(web):
    date = str(datetime.datetime.now().date())
    cursor = client['personal_project'][web]
    query = cursor.find({}, {'_id': 0})
    data = [x for x in query]
    data = json.dumps(data, ensure_ascii=False)
    data = (f'{date}_{web}.json', data)
    return data


def upload_s3(arr):
    for up in arr:
        if up[1] != '[]':
            S3_object = S3.Object('hotelmongodata', up[0])
            S3_object.put(Body=bytes(up[1].encode('UTF-8')))
        else:
            print(f"{up[0]} is empty")


def data_transfer():
    hotels = pack_data('hotels')
    booking = pack_data('booking')
    agoda = pack_data('agoda')
    upload = [hotels, booking, agoda]
    upload_s3(upload)
    bucket = S3.Bucket('hotelmongodata')
    check = []
    for obj in bucket.objects.all():
        check.append(obj.key)
    db = client['personal_project']
    if hotels[0] in check:
        db['hotels'].drop()
    if booking[0] in check:
        db['booking'].drop()
    if agoda[0] in check:
        db['agoda'].drop()


def store_start_time_dashboard():
    date = datetime.datetime.now().date()
    start_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    mysql_db = pool.get_conn()
    dash_time = [date, 0, 1, start_time]
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    sql = """
            INSERT INTO dash_time (date, resource, pipe, start) VALUES (%s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE start = VALUES (start)
            """
    cursor.execute(sql, dash_time)
    mysql_db.commit()
    pool.release(mysql_db)


if __name__ == '__main__':
    data_transfer()
    store_start_time_dashboard()
    os._exit(0)

