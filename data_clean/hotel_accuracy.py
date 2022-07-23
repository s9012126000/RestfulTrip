from config.mysql_config import *
import pandas as pd
import datetime
import re
mysql_db = pool.get_conn()


def count_repeat_hotel():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("SELECT resource, url FROM resources")
    urls = cursor.fetchall()
    mysql_db.commit()
    pat = re.compile('https[\S]+\?')
    hotel = [(re.match(pat, x['url']).group(), 1) for x in urls if x['resource'] == 1]
    booking = [(re.match(pat, x['url']).group(), 1) for x in urls if x['resource'] == 2]
    agoda = [(re.match(pat, x['url']).group(), 1) for x in urls if x['resource'] == 3]

    hotel_df = pd.DataFrame(hotel, columns=['url', 'count'])
    booking_df = pd.DataFrame(booking, columns=['url', 'count'])
    agoda_df = pd.DataFrame(agoda, columns=['url', 'count'])

    hotel_df = hotel_df.groupby('url').sum().reset_index()
    hotel_df = hotel_df[hotel_df['count'] > 1]
    hotel_err = len(hotel_df)

    booking_df = booking_df.groupby('url').sum().reset_index()
    booking_df = booking_df[booking_df['count'] > 1]
    booking_err = len(booking_df)

    agoda_df = agoda_df.groupby('url').sum().reset_index()
    agoda_df = agoda_df[agoda_df['count'] > 1]
    agoda_err = len(agoda_df)

    tol_err = hotel_err + booking_err + agoda_err

    cursor.execute("SELECT count(*) as c FROM hotels")
    tol = cursor.fetchone()
    mysql_db.commit()

    accuracy = round(((tol['c']-tol_err)/tol['c']) * 100, 2)

    print(f'Repeat data: {tol_err}')
    print(f'Accuracy: {accuracy}%')
    cursor.execute("SELECT * FROM dash_time ORDER BY date DESC")
    date = cursor.fetchone()['date']
    mysql_db.commit()
    dash_accu = (date, hotel_err, agoda_err, booking_err, tol_err, tol['c'])
    cursor.execute("INSERT INTO dash_accu VALUES (%s, %s, %s, %s, %s, %s)", dash_accu)
    mysql_db.commit()


def store_end_time_dashboard():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("SELECT * FROM dash_time ORDER BY date DESC")
    last_row = cursor.fetchone()
    if last_row['end'] is None:
        date = last_row['date']
        end_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        sql = f"UPDATE dash_time SET end = '{end_time}' WHERE date = '{date}'"
        cursor.execute(sql)
        mysql_db.commit()
        pool.release(mysql_db)


if __name__ == '__main__':
    count_repeat_hotel()
    store_end_time_dashboard()
    os._exit(0)