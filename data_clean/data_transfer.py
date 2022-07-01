from config.mongo_config import *
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
        S3_object = S3.Object('hotelmongodata', up[0])
        S3_object.put(Body=bytes(up[1].encode('UTF-8')))


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
    name_ls = [hotels[0], booking[0], agoda[0]]
    if all(name in check for name in name_ls):
        db = client['personal_project']
        db['hotels'].drop()
        db['booking'].drop()
        db['agoda'].drop()


if __name__ == '__main__':
    data_transfer()


