from config.mongo_config import *
from config.crawler_config import *
import time
import random


def fetching(link):
    headers["User-Agent"] = UserAgent().random
    hotel_req = requests.get(link, headers=headers, allow_redirects=False)
    hotel_soup = BeautifulSoup(hotel_req.text, "html.parser")
    name = hotel_soup.find(id="hp_hotel_name").text
    address = hotel_soup.find(id="showMap2").findAll("span")[1].text
    try:
        rating = hotel_soup.find(
            "div", attrs={"data-testid": "review-score-right-component"}
        ).text
    except AttributeError:
        rating = "No enough record"
    img = hotel_soup.find("a", attrs={"data-preview-image-layout": "main"}).find("img")[
        "src"
    ]
    des = hotel_soup.find(id="property_description_content").text
    try:
        star = len(
            hotel_soup.find("span", attrs={"data-testid": "rating-stars"}).findAll(
                "span"
            )
        )
    except AttributeError:
        star = 0
    pack = {
        "name": name,
        "url": link,
        "address": address,
        "rating": rating,
        "img": img,
        "des": des,
        "star": star,
    }
    print(f"success: {name}")
    hotel_ls.append(pack)
    time.sleep(random.randint(1, 2))


def re_crawl_data(url_ls):
    for url in url_ls:
        try:
            fetching(url)
        except AttributeError as m:
            for i in range(5):
                try:
                    print(f"attempt {i}")
                    print(m)
                    time.sleep(10)
                    fetching(url)
                    break
                except AttributeError:
                    print(f"attempt {i} fail")
                    if i == 4:
                        with open("logs/booking_lost_data_re.txt", "a") as e:
                            e.write(url)
                        print(f"lost data")
                    pass
            pass


if __name__ == "__main__":
    hotel_ls = []
    col = client["personal_project"]["booking"]
    db_count = col.estimated_document_count()
    with open("logs/booking_lost_data.txt", "r") as f:
        remain_ls = f.read().replace("\n", "").split("url:")
        remain_ls.pop(0)
    re_crawl_data(remain_ls)
    col.insert_many(hotel_ls, bypass_document_validation=True)
    new_count = col.estimated_document_count()
    if hotel_ls and (new_count - db_count) == len(remain_ls):
        with open("logs/booking_lost_data.txt", "w") as f:
            f.write("")
