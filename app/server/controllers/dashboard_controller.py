from flask import render_template
from app.server.models.dashboard_model import *
from app.server import app
import json


@app.route("/admin/dashboard")
def dashboard():
    return render_template("dash.html")


@app.route("/admin/fetch_data", methods=["POST"])
def fetch_data():
    hotel_pack = get_hotel_data()
    price_pack = get_hotel_price()
    time_pack = get_crawler_time()
    accuracy_pack = get_hotel_accuracy()
    text_pack = get_hotel_count()
    data_pack = {
        "hotel_pack": hotel_pack,
        "price_pack": price_pack,
        "time_pack": time_pack,
        "accu_pack": accuracy_pack,
        "text_pack": text_pack,
    }
    data_pack = json.dumps(data_pack)
    return data_pack
