from flask import Flask, render_template, request
from config.mysql_config import *
from dotenv import load_dotenv
from math import ceil
import datetime
import os
import re


load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
app.config['JSON_AS_ASCII'] = False
DEBUG, PORT, HOST = True, 8080, '0.0.0.0'
MyDb = pool.get_conn()


@app.route('/')
def main():
    checkin = datetime.datetime.now().date().isoformat()
    checkin_limit = (datetime.datetime.now() + datetime.timedelta(days=30)).date().isoformat()
    checkout = (datetime.datetime.now() + datetime.timedelta(days=1)).date().isoformat()
    checkout_limit = (datetime.datetime.now() + datetime.timedelta(days=31)).date().isoformat()
    return render_template('index.html',
                           checkin=checkin,
                           checkin_limit=checkin_limit,
                           checkout=checkout,
                           checkout_limit=checkout_limit)


@app.route('/hotels')
def hotels():
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    dest = request.args.get("dest")
    dest = dest.strip()
    dest = dest.strip("'")
    checkin = request.args.get("checkin")
    checkout = request.args.get("checkout")
    person = request.args.get("person")
    page = request.args.get("page")
    user_send = {
        'dest': dest,
        'checkin': checkin,
        'checkout': checkout,
        'person': person
    }

    cursor.execute(f"SELECT count(*) AS count FROM hotels WHERE address LIKE '%{dest}%'")
    count = cursor.fetchone()['count']
    MyDb.commit()
    msg = f'為您搜出 {count} 間旅館'
    page_tol = ceil(count/15)
    if page is None:
        page = 1

    date_tag = True
    if checkin != '' and checkout != '':
        che_in = datetime.datetime.strptime(checkin, "%Y-%m-%d")
        che_out = datetime.datetime.strptime(checkout, "%Y-%m-%d")
        if che_out < che_in:
            date_tag = False
        elif (che_out - che_in).days > 30:
            date_tag = False
    else:
        date_tag = False

    person_tag = True
    try:
        person = int(person)
    except:
        person_tag = False

    dest_tag = True
    if dest == '':
        dest_tag = False
    elif re.search(r'[\dA-Za-z%_&\-~@#$^*(){}|\[\]?><.=+;:"]+', dest):
        dest_tag = False

    if count and person_tag and date_tag and dest_tag and page_tol >= int(page):
        cursor.execute(
            f"SELECT * FROM hotels WHERE address like '%{dest}%' ORDER BY id LIMIT {(int(page) - 1) * 15},15")
        hotel_data = cursor.fetchall()
        MyDb.commit()
        hid = [x['id'] for x in hotel_data]
        hid = tuple(hid)
        if len(hid) == 1:
            hid = f'({hid[0]})'

        cursor.execute(f'select hotel_id, image from images where hotel_id in {hid}')
        image_data = cursor.fetchall()
        MyDb.commit()
        image_dt = {}
        for img in image_data:
            try:
                image_dt[img['hotel_id']].append(img['image'])
            except KeyError:
                image_dt[img['hotel_id']] = []
                image_dt[img['hotel_id']].append(img['image'])
        checkout = datetime.datetime.strptime(checkout, "%Y-%m-%d")
        checkout = (checkout - datetime.timedelta(days=1)).date().isoformat()
        if int(person) < 5:
            person_sql = f'between {person} and {int(person) + 1}'
        elif 5 <= int(person) <= 7:
            person_sql = 'between 5 and 7'
        elif 7 < int(person) <= 10:
            person_sql = 'between 7 and 10'
        else:
            person_sql = f'>={person}'
        cursor.execute(
            f"""
            SELECT re.id, re.hotel_id, re.resource, p.price, re.url
            FROM resources as re 
            inner join price as p on re.id = p.resource_id
            where p.date between '{checkin}' and '{checkout}' and re.hotel_id in {tuple(hid)} and p.person {person_sql} 
            order by hotel_id 
            """
        )
        price = cursor.fetchall()
        price_sum = {}
        checkout = (datetime.datetime.strptime(checkout, '%Y-%m-%d').date()
                    + datetime.timedelta(days=1)).isoformat()
        for p in price:
            if p['resource'] == 1:
                p['url'] = p['url'].replace('chkin=2022-10-01', f'chkin={checkin}') \
                    .replace('chkout=2022-10-02', f'chkout={checkout}')
            elif p['resource'] == 2:
                p['url'] = p['url'].replace('checkin=2022-06-18', f'checkin={checkin}') \
                    .replace('checkout=2022-06-19', f'checkout={checkout}')
            else:
                day_delta = (datetime.datetime.strptime(checkout, '%Y-%m-%d').date() -
                             datetime.datetime.strptime(checkin, '%Y-%m-%d').date()).days
                p['url'] = p['url'].replace('checkIn=2022-06-28', f'checkIn={checkin}') \
                    .replace('los=1', f'los={day_delta}')
            try:
                price_sum[p['id']]['price'] += p['price']
                price_sum[p['id']]['count'] += 1
            except KeyError:
                price_sum[p['id']] = p
                price_sum[p['id']]['count'] = 1
        price_dt = {}
        for p in price_sum.values():
            try:
                price_dt[p['hotel_id']][p['resource']] = (format(int(p['price'] / p['count']), ','), p['url'])
            except KeyError:
                price_dt[p['hotel_id']] = {}
                price_dt[p['hotel_id']][p['resource']] = (format(int(p['price'] / p['count']), ','), p['url'])
    else:
        che_in = datetime.datetime.strptime(checkin, "%Y-%m-%d")
        che_out = datetime.datetime.strptime(checkout, "%Y-%m-%d")
        hotel_data = ''
        image_dt = ''
        price_dt = ''
        if dest == '':
            msg = "請您輸入想去的地點"
        elif checkin == '':
            msg = "請您輸入入住日期"
        elif checkout == '':
            msg = "請您輸入退房日期"
        elif checkout < checkin:
            msg = "請您輸入有效日期"
        elif (che_out - che_in).days > 30:
            msg = "很抱歉，RestfulTrip 僅提供30天即時價格"
        elif person == '':
            msg = "請您輸入人數"
        elif type(person) is not int:
            msg = "請您輸入有效人數"
        elif 0 < page_tol < int(page):
            msg = '很抱歉，無法獲取該頁資訊'
        else:
            msg = f"很抱歉，我們找不到 '{dest}'"

    checkin = datetime.datetime.now().date().isoformat()
    checkin_limit = (datetime.datetime.now() + datetime.timedelta(days=30)).date().isoformat()
    checkout = (datetime.datetime.now() + datetime.timedelta(days=1)).date().isoformat()
    checkout_limit = (datetime.datetime.now() + datetime.timedelta(days=31)).date().isoformat()
    return render_template('hotel.html',
                           hotel_data=hotel_data,
                           image_data=image_dt,
                           price=price_dt,
                           msg=msg,
                           user_send=user_send,
                           page=page,
                           page_tol=page_tol,
                           checkin=checkin,
                           checkin_limit=checkin_limit,
                           checkout=checkout,
                           checkout_limit=checkout_limit
                           )


if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)
