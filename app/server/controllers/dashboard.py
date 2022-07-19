from flask import render_template
from config.mysql_config import *
from app.server import app
import json

MyDb = pool.get_conn()


@app.route('/admin/dashboard')
def dashboard():
    return render_template('dash.html')


@app.route('/admin/fetch_data', methods=['GET'])
def fetch_data():
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute("SELECT date, tol FROM dash_hotels WHERE resource = 1")
    hotel = cursor.fetchall()
    MyDb.commit()
    cursor.execute("SELECT date, tol FROM dash_hotels WHERE resource = 2")
    booking = cursor.fetchall()
    MyDb.commit()
    cursor.execute("SELECT date, tol FROM dash_hotels WHERE resource = 3")
    agoda = cursor.fetchall()
    MyDb.commit()
    hotel = {
        'date': [str(x['date']) for x in hotel],
        'tol': [x['tol'] for x in hotel]
    }
    booking = {
        'date': [str(x['date']) for x in booking],
        'tol': [x['tol'] for x in booking]
    }
    agoda = {
        'date': [str(x['date']) for x in agoda],
        'tol': [x['tol'] for x in agoda]
    }
    tol = [hotel['tol'][i] + booking['tol'][i] + agoda['tol'][i] for i in range(len(hotel['date']))]
    hotel_pack = {
        'hotel': hotel,
        'booking': booking,
        'agoda': agoda,
        'tol': tol
    }

    cursor.execute("SELECT * FROM dash_price")
    price = cursor.fetchall()
    MyDb.commit()
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

    cursor.execute("SELECT * FROM dash_time")
    pipe_time = cursor.fetchall()
    MyDb.commit()
    pipe_time = [
        {'date': str(x['date']),
         'spend': round((x['end'] - x['start']).seconds / 3600, 3),
         'pipe': x['pipe'],
         'resource': x['resource']
         } for x in pipe_time
    ]
    pipe1_time = [x for x in pipe_time if x['pipe'] == 1]
    pipe2_time = [x for x in pipe_time if x['pipe'] == 2]

    time_pack = {
        'pipe1': {'date': [x['date'] for x in pipe1_time],
                  'spend': [x['spend'] for x in pipe1_time]},
        'pipe2': {
            'hotel': {
                'date': [x['date'] for x in pipe2_time if x['resource'] == 1],
                'spend': [x['spend'] for x in pipe2_time if x['resource'] == 1]
            },
            'booking': {
                'date': [x['date'] for x in pipe2_time if x['resource'] == 2],
                'spend': [x['spend'] for x in pipe2_time if x['resource'] == 2]
            },
            'agoda': {
                'date': [x['date'] for x in pipe2_time if x['resource'] == 3],
                'spend': [x['spend'] for x in pipe2_time if x['resource'] == 3]
            },
        }
    }

    cursor.execute("""
        SELECT * FROM dash_accu as da
        INNER JOIN dash_hotels as dh
        ON da.date = dh.date
        WHERE da.date > '2022-07-15' 
        """)
    accu = cursor.fetchall()
    MyDb.commit()
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

    cursor.execute("SELECT count(*) as c FROM price")
    price = cursor.fetchone()['c']
    price = format(price, ',')
    MyDb.commit()
    cursor.execute("SELECT count(*) as c FROM hotels")
    hotel = cursor.fetchone()['c']
    hotel = format(hotel, ',')

    text_pack = {'price': price, 'hotel': hotel}

    pack = {
        'hotel_pack': hotel_pack,
        'price_pack': price_pack,
        'time_pack': time_pack,
        'accu_pack': accu_pack,
        'text_pack': text_pack
    }

    pack = json.dumps(pack)
    return pack