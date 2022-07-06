from config.mongo_config import *
from config.crawler_config import *
from math import ceil

import threading
import datetime
import random
import json
import time
import queue


def get_region_url():
    with open('jsons/divisions.json') as d:
        divisions = json.load(d)
    ext = ['花蓮市', '台東市', '宜蘭市', '台南縣']
    divisions.extend(ext)
    links = []
    for div in divisions:
        if '臺' in div:
            div = div.replace('臺', '台')
        print(div)
        driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=chrome_options)
        driver.get('https://www.booking.com/searchresults.zh-tw.html')
        input_elm = WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.XPATH, "//input[@name='ss']"))
        )
        input_elm.send_keys(div)
        driver.find_element(By.XPATH, "//div[@data-component='arp-searchbox']/div/div/form/div/div[6]").click()
        hotel_num = int(WebDriverWait(driver, 10).until(
            ec.visibility_of_element_located((By.XPATH, "//div[@data-component='arp-header']/div/div/div/h1"))
        ).text.split(' ')[1])
        url = driver.current_url
        driver.close()
        links.append((url, hotel_num))
    return links


class Worker(threading.Thread):
    def __init__(self, worker_num):
        threading.Thread.__init__(self)
        self.worker_num = worker_num

    def run(self):
        while not job_queue.empty():
            self.get_booking_hotels(job_queue.get())

    def get_booking_hotels(self, region):
        col = client['personal_project']['booking']
        hotel_num = region[1]
        url = region[0]
        iter_count = ceil(hotel_num / 25)
        offset = 0
        hotel_ls = []
        for count in range(iter_count):
            def get_card():
                headers['User-Agent'] = UserAgent().random
                page_url = url + f'&offset={offset}'
                url_req = requests.get(page_url, headers=headers, allow_redirects=False)
                url_soup = BeautifulSoup(url_req.text, 'html.parser')
                cards = url_soup.find(id='search_results_table').findAll('div', attrs={"data-testid": "property-card"})
                time.sleep(1)
                return cards
            try:
                property_card = get_card()
            except AttributeError:
                tag = ''
                property_card = ''
                for i in range(5):
                    try:
                        print(f'card attempt {i}')
                        time.sleep(10)
                        property_card = get_card()
                        tag = 'success'
                        break
                    except AttributeError:
                        print(f'card attempt {i} fail')
                        if i == 4:
                            tag = 'fail'
                if tag == 'fail':
                    with open('logs/hotels/booking_lost_card.log', 'a') as e:
                        url = url + f'&offset={offset}'
                        e.write('url:\n' + url + '\n')
                    print(f"lost card")
                    break
            for card in property_card:
                def fetching():
                    link = card.find('a')['href']
                    headers['User-Agent'] = UserAgent().random
                    hotel_req = requests.get(link, headers=headers, allow_redirects=False)
                    hotel_soup = BeautifulSoup(hotel_req.text, 'html.parser')
                    name = hotel_soup.find(id='hp_hotel_name').text
                    address = hotel_soup.find(id='showMap2').findAll('span')[1].text
                    try:
                        rating = hotel_soup.find('div', attrs={"data-testid": "review-score-right-component"}).text
                    except AttributeError:
                        rating = 'No enough record'
                    img = hotel_soup.find('a', attrs={"data-preview-image-layout": "main"}).find('img')['src']
                    des = hotel_soup.find(id='property_description_content').text
                    try:
                        star = len(hotel_soup.find('span', attrs={"data-testid": "rating-stars"}).findAll('span'))
                    except AttributeError:
                        star = 0
                    pack = {
                        'name': name,
                        'url': link,
                        'address': address,
                        'rating': rating,
                        'img': img,
                        'des': des,
                        'star': star
                    }
                    print(f'{self.worker_num} success: {name}')
                    hotel_ls.append(pack)
                    time.sleep(random.randint(1, 2))
                try:
                    fetching()
                except AttributeError as m:
                    for i in range(5):
                        try:
                            print(f'attempt {i}')
                            time.sleep(10)
                            fetching()
                            break
                        except AttributeError:
                            print(f'attempt {i} fail')
                            if i == 4:
                                with open('logs/hotels/booking_lost_data.log', 'a') as e:
                                    lnk = card.find('a')['href']
                                    e.write('url:\n' + str(lnk) + '\n')
                                print(f"lost data")
            offset += 25
            time.sleep(random.randint(1, 3))
        col.insert_many(hotel_ls, bypass_document_validation=True)
        print(f'store successfully: {len(hotel_ls)}')


if __name__ == '__main__':
    # booking_urls = get_region_url()
    # with open('jsons/booking_regions_urls.json', 'w') as f:
    #     json.dump(booking_urls, f)
    START_TIME = datetime.datetime.now()
    print(f"booking started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")

    with open('jsons/booking_regions_urls.json', 'r') as u:
        urls = json.load(u)
    job_queue = queue.Queue()
    for job in urls:
        job_queue.put(job)

    workers = []
    worker_count = 4
    for i in range(worker_count):
        num = i + 1
        worker = Worker(num)
        workers.append(worker)

    for worker in workers:
        worker.start()

    for worker in workers:
        worker.join()

    END_TIME = datetime.datetime.now()
    print(f"booking started at {START_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"booking finished at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"booking cost {(END_TIME - START_TIME).seconds // 60} minutes")

