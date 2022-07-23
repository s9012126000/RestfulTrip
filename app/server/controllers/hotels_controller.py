from flask import render_template, request
from app.server.models.hotels_model import *
from app.server.utils.input_checker import *
from app.server.utils.utils import *
from app.server import app
from math import ceil


@app.route("/")
def main():
    checkin, checkin_limit, checkout, checkout_limit = get_date_limitation(14)
    return render_template(
        "index.html",
        checkin=checkin,
        checkin_limit=checkin_limit,
        checkout=checkout,
        checkout_limit=checkout_limit,
    )


@app.route("/hotels")
def hotels():
    dest = request.args.get("dest").strip().strip("'").strip('"')
    checkin = request.args.get("checkin")
    checkout = request.args.get("checkout")
    person = request.args.get("person")
    page = request.args.get("page")
    send_back = {
        "dest": dest,
        "checkin": checkin,
        "checkout": checkout,
        "person": person,
    }
    count = get_hotel_count(dest)
    msg = f"為您搜出 {count} 間旅館"
    page_tol = ceil(count / 15)
    if page is None or page == "":
        page = 1
    page, page_tag = check_input_page(page, page_tol)
    date_tag, date_limit = check_input_date(checkin, checkout)
    person, person_tag = check_input_person(person)
    dest_tag = check_input_dest(dest)
    if count and person_tag and date_tag and dest_tag and page_tag:
        hotel_data = get_hotel_data(dest, page)
        hotel_id = tuple([x["id"] for x in hotel_data])
        if len(hotel_id) == 1:
            hotel_id = f"({hotel_id[0]})"
        images = get_hotel_image(hotel_id)
        prices = get_hotel_price(checkin, checkout, hotel_id, person)
    else:
        hotel_data = ""
        images = ""
        prices = ""
        if dest == "":
            msg = "請您輸入想去的地點"
        elif checkin == "":
            msg = "請您輸入入住日期"
        elif checkout == "":
            msg = "請您輸入退房日期"
        elif not date_limit:
            msg = "很抱歉，RestfulTrip 僅提供14天即時價格"
        elif not date_tag:
            msg = "請您輸入有效日期"
        elif person == "":
            msg = "請您輸入人數"
        elif type(person) is not int or person <= 0:
            msg = "請您輸入有效人數"
        elif type(page) is not int:
            msg = "很抱歉，無法獲取該頁資訊"
        elif 0 < page_tol < page or page <= 0:
            msg = "很抱歉，無法獲取該頁資訊"
        else:
            msg = f"很抱歉，我們找不到 '{dest}'"
    checkin, checkin_limit, checkout, checkout_limit = get_date_limitation(14)
    return render_template(
        "hotel.html",
        hotel_data=hotel_data,
        image_data=images,
        price=prices,
        msg=msg,
        user_send=send_back,
        page=page,
        page_tol=page_tol,
        checkin=checkin,
        checkin_limit=checkin_limit,
        checkout=checkout,
        checkout_limit=checkout_limit,
    )
