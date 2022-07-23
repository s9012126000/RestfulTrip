from config.mysql_config import *
import datetime

mysql_db = pool.get_conn()


def get_hotel_count(dest):
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(
        f"SELECT count(*) AS count FROM hotels WHERE name like '%{dest}%' OR address LIKE '%{dest}%'"
    )
    count = cursor.fetchone()["count"]
    mysql_db.commit()
    return count


def get_hotel_data(dest, page):
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(
        f"""
        SELECT * FROM hotels WHERE name like '%{dest}%' OR address like '%{dest}%'
        ORDER BY id LIMIT {(int(page) - 1) * 15},15
        """
    )
    hotel_data = cursor.fetchall()
    mysql_db.commit()
    return hotel_data


def get_hotel_image(hid):
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    cursor.execute(f"select hotel_id, image from images where hotel_id in {hid}")
    image_data = cursor.fetchall()
    mysql_db.commit()
    images = {}
    for img in image_data:
        try:
            images[img["hotel_id"]].append(img["image"])
        except KeyError:
            images[img["hotel_id"]] = []
            images[img["hotel_id"]].append(img["image"])
    return images


def get_hotel_price(checkin, checkout, hid, person):
    mysql_db.ping(reconnect=True)
    cursor = mysql_db.cursor()
    if int(person) < 5:
        person_sql = f"between {person} and {int(person) + 1}"
    elif 5 <= int(person) <= 7:
        person_sql = "between 5 and 7"
    elif 7 < int(person) <= 10:
        person_sql = "between 7 and 10"
    else:
        person_sql = f">={person}"
    cursor.execute(
        f"""
        SELECT re.id, re.hotel_id, re.resource, p.price, re.url
        FROM resources as re 
        inner join price as p on re.id = p.resource_id
        where p.date between '{checkin}' 
            and '{checkout}' 
            and re.hotel_id in {tuple(hid)} 
            and p.person {person_sql} 
        """
    )
    prices = cursor.fetchall()
    mysql_db.commit()
    price_sum = {}
    for price in prices:
        if price["resource"] == 1:
            price["url"] = (
                price["url"]
                .replace("chkin=2022-10-01", f"chkin={checkin}")
                .replace("chkout=2022-10-02", f"chkout={checkout}")
            )
        elif price["resource"] == 2:
            price["url"] = (
                price["url"]
                .replace("checkin=2022-06-18", f"checkin={checkin}")
                .replace("checkout=2022-06-19", f"checkout={checkout}")
            )
        else:
            day_delta = (
                datetime.datetime.strptime(checkout, "%Y-%m-%d").date()
                - datetime.datetime.strptime(checkin, "%Y-%m-%d").date()
            ).days
            price["url"] = (
                price["url"]
                .replace("checkIn=2022-06-28", f"checkIn={checkin}")
                .replace("los=1", f"los={day_delta}")
            )
        try:
            price_sum[price["id"]]["price"] += price["price"]
            price_sum[price["id"]]["count"] += 1
        except KeyError:
            price_sum[price["id"]] = price
            price_sum[price["id"]]["count"] = 1
    prices = {}
    for p in price_sum.values():
        try:
            prices[p["hotel_id"]][p["resource"]] = (
                format(int(p["price"] / p["count"]), ","),
                p["url"],
            )
        except KeyError:
            prices[p["hotel_id"]] = {}
            prices[p["hotel_id"]][p["resource"]] = (
                format(int(p["price"] / p["count"]), ","),
                p["url"],
            )
    return prices
