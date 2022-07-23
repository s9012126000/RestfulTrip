from config.mysql_config import *

mysql_db = pool.get_conn()


def get_hotel_data():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("SELECT date, tol, resource FROM dash_hotels ORDER BY date DESC LIMIT 15")
    hotel_data = cursor.fetchall()
    hotel_data = sorted(hotel_data, key=lambda x: x['date'])
    mysql_db.commit()
    hotels = {
        'date': [str(x['date']) for x in hotel_data if x['resource'] == 1],
        'tol': [x['tol'] for x in hotel_data if x['resource'] == 1]
    }
    booking = {
        'date': [str(x['date']) for x in hotel_data if x['resource'] == 2],
        'tol': [x['tol'] for x in hotel_data if x['resource'] == 2]
    }
    agoda = {
        'date': [str(x['date']) for x in hotel_data if x['resource'] == 3],
        'tol': [x['tol'] for x in hotel_data if x['resource'] == 3]
    }
    tol = [hotels['tol'][i] + booking['tol'][i] + agoda['tol'][i] for i in range(len(hotels['date']))]
    hotel_pack = {
        'hotel': hotels,
        'booking': booking,
        'agoda': agoda,
        'tol': tol
    }
    return hotel_pack


def get_hotel_price():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("SELECT * FROM dash_price ORDER BY date DESC LIMIT 15")
    price = cursor.fetchall()
    price = sorted(price, key=lambda x: x['date'])
    mysql_db.commit()
    price_pack = {
        'hotel': {
            'date': [str(x['date']) for x in price if x['resource'] == 1],
            'price': [x['price'] for x in price if x['resource'] == 1]
        },
        'booking': {
            'date': [str(x['date']) for x in price if x['resource'] == 2],
            'price': [x['price'] for x in price if x['resource'] == 2]
        },
        'agoda': {
            'date': [str(x['date']) for x in price if x['resource'] == 3],
            'price': [x['price'] for x in price if x['resource'] == 3]
        },
    }
    return price_pack


def get_crawler_time():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("SELECT * FROM dash_time WHERE pipe = 1 AND end IS NOT null ORDER BY date DESC LIMIT 5")
    pipe1_time = cursor.fetchall()
    pipe1_time = sorted(pipe1_time, key=lambda x: x['date'])
    mysql_db.commit()
    cursor.execute("SELECT * FROM dash_time WHERE pipe = 2 AND end IS NOT null ORDER BY date DESC LIMIT 15")
    pipe2_time = cursor.fetchall()
    pipe2_time = sorted(pipe2_time, key=lambda x: x['date'])
    mysql_db.commit()

    time_pack = {
        'pipe1': {'date': [str(x['date']) for x in pipe1_time],
                  'spend': [round((x['end'] - x['start']).seconds / 3600, 3) for x in pipe1_time]},
        'pipe2': {
            'hotel': {
                'date': [str(x['date']) for x in pipe2_time if x['resource'] == 1],
                'spend': [round((x['end'] - x['start']).seconds / 3600, 3) for x in pipe2_time if x['resource'] == 1]
            },
            'booking': {
                'date': [str(x['date']) for x in pipe2_time if x['resource'] == 2],
                'spend': [round((x['end'] - x['start']).seconds / 3600, 3) for x in pipe2_time if x['resource'] == 2]
            },
            'agoda': {
                'date': [str(x['date']) for x in pipe2_time if x['resource'] == 3],
                'spend': [round((x['end'] - x['start']).seconds / 3600, 3) for x in pipe2_time if x['resource'] == 3]
            },
        }
    }
    return time_pack


def get_hotel_accuracy():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("""
        SELECT * FROM dash_accu as da
        INNER JOIN dash_hotels as dh
        ON da.date = dh.date
        WHERE da.date > '2022-07-15' 
        """)
    accu = cursor.fetchall()
    mysql_db.commit()
    accu_pack = {
        'hotel': {
            "date": [str(x['date']) for x in accu if x['resource'] == 1],
            "accu": [round(((x['tol'] - x['hotel_err']) / x['tol']) * 100, 2)
                     for x in accu if x['resource'] == 1]
        },
        'booking': {
            "date": [str(x['date']) for x in accu if x['resource'] == 2],
            "accu": [round(((x['tol'] - x['booking_err']) / x['tol']) * 100, 2)
                     for x in accu if x['resource'] == 2]
        },
        'agoda': {
            "date": [str(x['date']) for x in accu if x['resource'] == 3],
            "accu": [round(((x['tol'] - x['agoda_err']) / x['tol']) * 100, 2)
                     for x in accu if x['resource'] == 3]
        },
        'total': {
            "date": [str(x['date']) for x in accu if x['resource'] == 1],
            "accu": [round(((x['tol_num'] - x['repeat_num']) / x['tol_num']) * 100, 2)
                     for x in accu if x['resource'] == 1]
        }
    }
    return accu_pack


def get_hotel_count():
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute("SELECT count(*) as c FROM price")
    price = cursor.fetchone()['c']
    price = format(price, ',')
    mysql_db.commit()
    cursor.execute("SELECT count(*) as c FROM hotels")
    hotel = cursor.fetchone()['c']
    hotel = format(hotel, ',')
    text_pack = {'price': price, 'hotel': hotel}
    return text_pack