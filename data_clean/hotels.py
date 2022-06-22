from personal_project.config.mongo_config import *
from personal_project.config.mysql_config import *
from difflib import SequenceMatcher
from pprint import pprint

import pandas as pd
import time
import re


def replace_all(text, dt):
    for i, j in dt.items():
        text = text.replace(i, j)
    return text


def hotel_com_clean():
    col = client['personal_project']['hotelcom']
    query = col.find({}, {'_id': 0})
    data = [x for x in query]
    check_ls = []
    hotel_ls = []
    name_ls = []
    for d in data:
        identifier = d['detail']
        if identifier in check_ls:
            continue
        else:
            name = d['detail'].split('\n')[0]
            if name in ['VIP Access', '整棟度假屋', '整間出租公寓', '整間木屋']:
                part = 1
            else:
                part = 0
            name = d['detail'].split('\n')[part]
            address = d['address']
            if name in name_ls:
                name = name + '-' + address.split(' ')[0]
            name_ls.append(name)
            des = d['detail'].split('\n')[-1]
            try:
                star = float(re.search(r"\d\.\d", d['detail']).group())
            except AttributeError:
                star = 0.0
            img = d['img']
            url = d['url']
            rating = '，來自 '.join(d['rating'].split('\n')[0:2])
            check_ls.append(identifier)
            pack = {
                'name': name,
                'address': address,
                'des': des,
                'resource': 1,
                'star': star,
                'url': url,
                'rating': rating,
                'img': img
            }
            hotel_ls.append(pack)

    return hotel_ls


def booking_com_clean():
    col = client['personal_project']['bookingcom']
    query = col.find({}, {'_id': 0})
    data = [x for x in query]
    check_ls = []
    hotel_ls = []
    for d in data:
        identifier = d['name']
        if identifier in check_ls:
            continue
        else:
            name = d['name'].split('\n')[-2]
            address = d['address'].strip()
            des = d['des'].strip().replace('\n', '')
            star = d['star']
            img = d['img']
            url = d['url']
            rating = d['rating']
            check_ls.append(identifier)
            pack = {
                'name': name,
                'address': address,
                'des': des,
                'resource': 2,
                'star': star,
                'url': url,
                'rating': rating,
                'img': img
            }
            hotel_ls.append(pack)
    return hotel_ls


def agoda_com_clean():
    col = client['personal_project']['agodacom']
    query = col.find({}, {'_id': 0})
    data = [x for x in query]
    check_ls = []
    hotel_ls = []
    for d in data:
        identifier = d['name']
        if identifier in check_ls:
            continue
        else:
            name = d['name']
            address = d['address']
            des = d['des']
            star = d['star']
            if 'pink' in star:
                star = 0.0
            elif 'orange' in star:
                try:
                    star = float('.'.join(re.search(r"star-(\d+)", star).group(1)))
                except AttributeError:
                    star = 0.0
            img = d['img']
            url = d['url']
            rating = d['rating'].replace('\n', '，')
            check_ls.append(identifier)
            pack = {
                'name': name,
                'address': address,
                'des': des,
                'resource': 3,
                'star': star,
                'url': url,
                'rating': rating,
                'img': img
            }
            hotel_ls.append(pack)
    return hotel_ls


# 比較飯店名稱 分出insert 跟 update
booking = booking_com_clean()
MyDb.ping(reconnect=True)
cursor = MyDb.cursor()
cursor.execute('SELECT * FROM hotels')
exist_hotel = cursor.fetchall()
MyDb.commit()
exist_df = pd.DataFrame(exist_hotel)
exist_name = exist_df['name']
replaces = {' ': '', '-': '', '(': '', ')': '', ',': '', '.': '', '．': ''}
exist_name = [
    replace_all(x, replaces).lower() for x in exist_name
]
exist_df['name'] = pd.Series(exist_name)
update_ls = []
insert_ls = []
for hotel in booking:
    e_name = replace_all(hotel['name'], replaces).lower()
    if e_name in exist_name:
        exist_row = exist_df[exist_df['name'] == e_name]
        e_id = exist_row['id'].values[0]
        update_ls.append((hotel, e_id))
        booking.remove(hotel)
        exist_name.remove(e_name)
for hotel in booking:
    name = replace_all(hotel['name'], replaces).lower()
    target_id = None
    r = 0
    for e_name in exist_name:
        rate = SequenceMatcher(None, name, e_name).quick_ratio()
        if rate > r:
            exist_row = exist_df[exist_df['name'] == e_name]
            r = rate
            target_id = exist_row['id'].values[0]
    if r > 0.8:
        exist_row = exist_df[exist_df['id'] == target_id]
        address = replace_all(hotel['address'], replaces)
        e_address = replace_all(exist_row['address'].values[0], replaces)
        address_rate = SequenceMatcher(None, address, e_address).quick_ratio()
        if address_rate > 0.2:
            update_ls.append((hotel, target_id))
            # print(name)
            # print(exist_row['name'].values[0], '\n')
        else:
            insert_ls.append(hotel)
    elif 0.5 < r <= 0.8:
        exist_row = exist_df[exist_df['id'] == target_id]
        address = replace_all(hotel['address'], replaces)
        e_address = replace_all(exist_row['address'].values[0], replaces)
        address_rate = SequenceMatcher(None, address, e_address).quick_ratio()
        if address_rate > 0.6:
            update_ls.append((hotel, target_id))
            # print(name)
            # print(exist_row['name'].values[0], '\n')
        else:
            insert_ls.append(hotel)
    else:
        insert_ls.append(hotel)
print(time.perf_counter())


# 處理 update
h_ls = []
img_ls = []
res_ls = []
for up in update_ls:
    hotel = up[0]
    exist_row = exist_df[exist_df['id'] == up[1]]
    hotel_pack = {'id': exist_row['id'].values[0]}
    if exist_row['address'].values[0] == 'non-provided':
        address = hotel['address']
        hotel_pack['address'] = address
    if len(hotel['des']) > len(exist_row['des']):
        des = hotel['des']
        hotel_pack['des'] = des
    if hotel['star'] != 0 and exist_row['star'].values[0] == 0.0:
        star = float(hotel['star'])
        hotel_pack['star'] = star
    img_pack = {
        'image': hotel['img'],
        'hotel_id': up[1]
    }
    resource_pack = {
        'resource': hotel['resource'],
        'url': hotel['url'],
        'rating': hotel['rating'],
        'hotel_id': up[1]
    }
    h_ls.append(hotel_pack)
    img_ls.append(img_pack)
    res_ls.append(resource_pack)
    # pprint(hotel_pack)


def insert_new(hotels):
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute("SELECT id FROM hotels ORDER BY id DESC LIMIT 1")
    last_id = cursor.fetchone()
    MyDb.commit()
    if not last_id:
        hotel_id = 0
    else:
        hotel_id = last_id['id']

    hotel_vals = []
    res_vals = []
    img_vals = []
    for hotel in hotels:
        hotel_id += 1
        hotel_val = (hotel_id, hotel['name'], hotel['address'], hotel['des'], hotel['star'])
        res_val = (hotel['resource'], hotel['url'], hotel['rating'], hotel_id)
        img_val = (hotel['img'], hotel_id)
        hotel_vals.append(hotel_val)
        res_vals.append(res_val)
        img_vals.append(img_val)

    h_place = ', '.join(['%s'] * len(hotel_vals[0]))
    r_place = ', '.join(['%s'] * len(res_vals[0]))
    i_place = ', '.join(['%s'] * len(img_vals[0]))
    hotel_sql = f"INSERT INTO hotels (id, name, address, des, star) VALUES ({h_place})"
    res_sql = f"INSERT INTO resources (resource, url, rating, hotel_id) VALUES ({r_place})"
    img_sql = f"INSERT INTO images (image, hotel_id) VALUES ({i_place})"

    cursor.executemany(hotel_sql, hotel_vals)
    cursor.executemany(res_sql, res_vals)
    cursor.executemany(img_sql, img_vals)
    MyDb.commit()


# a_sqls = []
# d_sqls = []
# s_sqls = []
# for h in h_ls:
#     try:
#         sql = f"WHEN {h['id']} THEN '{h['address']}'"
#         a_sqls.append(sql)
#     except KeyError:
#         pass
#     try:
#         sql = f"WHEN {h['id']} THEN '{h['des']}'"
#         d_sqls.append(sql)
#     except KeyError:
#         pass
#     try:
#         sql = f"WHEN {h['id']} THEN '{h['star']}'"
#         s_sqls.append(sql)
#     except KeyError:
#         pass
#
# address_sql = ' '.join(a_sqls)
# des_sql = ' '.join(d_sqls)
# star_sql = ' '.join(s_sqls)
#
#
# """
# UPDATE hotels
# SET address = (CASE id)
# """