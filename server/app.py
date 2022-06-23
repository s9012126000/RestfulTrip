import json

from flask import Flask, render_template, request, redirect, send_from_directory
from personal_project.config.mysql_config import *
from dotenv import load_dotenv
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('secret_key')
app.config['JSON_AS_ASCII'] = False
DEBUG, PORT, HOST = True, 8080, '0.0.0.0'


@app.route('/')
def main():
    MyDb.ping(reconnect=True)
    cursor = MyDb.cursor()
    cursor.execute('select hotels.*, images.image from hotels inner join images on hotels.id = images.hotel_id')
    a = cursor.fetchone()
    name = a['name']
    img = a['image']
    add = a['address']
    # b = json.dumps(a)

    return render_template('hotel.html', name=name, image=img, add=add)


if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)
