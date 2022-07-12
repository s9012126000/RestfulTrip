from crawler_config import *
from mysql_config import *
from pprint import pprint
import datetime
import json
import time
import pika
import sys
import re
import os

driver = webdriver.Chrome(ChromeDriverManager(version='104.0.5112.20').install(), options=options)

credentials = pika.credentials.PlainCredentials(
    username=os.getenv('rbt_user'),
    password=os.getenv('rbt_pwd')
)
conn_param = pika.ConnectionParameters(
    host=os.getenv('rbt_host'),
    port=5672,
    credentials=credentials
)
conn = pika.BlockingConnection(conn_param)
channel = conn.channel()


def main():
    channel.queue_declare(queue='hotels')

    def replace_all(text, dt):
        for i, j in dt.items():
            text = text.replace(i, j)
        return text

    def get_thirty_dates():
        date_ls = []
        for d in range(7):
            date = (datetime.datetime.now().date() + datetime.timedelta(days=d))
            date_ls.append(date)
        return date_ls

    def callback(ch, method, properties, body):
        db = pool.get_conn()
        url = json.loads(body.decode('UTF-8'))
        prices, empty = get_hotel_price(url)
        if prices:
            price_to_sql(prices, db)
            print(f"insert {url['hotel_id']} successfully")
        else:
            print(f"{url['hotel_id']} is empty")
        if empty['date']:
            empty_to_sql(empty, db)
        print(f"hotel {url['hotel_id']}: done")

    def get_hotel_price(link):
        date_ls = get_thirty_dates()
        uid = link['id']
        url = link['url']
        price_ls = []
        empty_date = []
        for date in date_ls:
            checkin = date
            checkout = date + datetime.timedelta(days=1)
            replaces = {
                'chkin=2022-10-01': f'chkin={checkin}',
                'chkout=2022-10-02': f'chkout={checkout}',
            }
            url_new = replace_all(url, replaces)
            try:
                driver.get(url_new)
                driver.execute_script("window.scrollTo(0, 800)")
                time.sleep(0.5)
                wait = WebDriverWait(driver, 1)
                cards = wait.until(ec.presence_of_element_located((By.ID, "Offers")))
                wait.until(ec.presence_of_all_elements_located((By.TAG_NAME, 'ul')))
                try:
                    empty = driver.find_element(By.XPATH, "//div[@data-stid='error-messages']").text
                    print(empty)
                    raise TimeoutException
                except NoSuchElementException:
                    pass
                wait.until(ec.presence_of_all_elements_located((By.XPATH, "//div[@data-stid='price-summary']")))
                room = cards.find_elements(By.TAG_NAME, 'ul')
                room = [int(re.search(r"最多可入住 (\d) 人", x.text).group(1)) for x in room]

                price = cards.find_elements(By.XPATH, "//div[@data-stid='price-summary']")
                price = [int(re.search(r"\d+", (x.text.replace(',', ''))).group())
                         for x in price]
                room = room[0:len(price)]
                price_dict = {}
                for i in range(len(room)):
                    try:
                        if price_dict[room[i]] > price[i]:
                            price_dict[room[i]] = price[i]
                    except KeyError:
                        price_dict[room[i]] = price[i]
                price_pack = [{
                    'date': date,
                    'price': price,
                    'resource_id': uid,
                    'person': person}
                    for person, price in price_dict.items()]
                pprint(price_pack)
                price_ls.extend(price_pack)
            except TimeoutException:
                print(f"{uid} is empty at {date}")
                empty_date.append(str(date))
        empty_pack = {
            'date': empty_date,
            'resource_id': uid
        }
        pprint(empty_pack)
        return price_ls, empty_pack

    channel.basic_consume(queue='hotels',
                          auto_ack=True,
                          on_message_callback=callback)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)