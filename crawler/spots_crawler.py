from config.mongo_config import *
from config.crawler_config import *

max_id = 4500
col = client["personal_project"]["spots"]
spots_ls = []
for sid in range(max_id):
    url = f"https://okgo.tw/butyview.html?id={sid}"
    req = requests.get(url, headers=headers)
    soup = BeautifulSoup(req.text, "html.parser")
    if soup.string == "window.location.href='Error.html';":
        continue
    name = soup.find("div", attrs={"class": "content"}).find("h2").text
    region = soup.find("div", attrs={"class": "content"}).find("strong").text
    address = (
        soup.find("div", attrs={"class": "content"})
        .find("br")
        .text.strip()
        .split(" ")[0]
    )
    des = (
        soup.find("div", attrs={"class": "content"})
        .find("br")
        .find("br")
        .find("br")
        .text.strip()
    )
    try:
        img = soup.find(id="Buty_View_PicSource").find("img")["src"]
    except AttributeError:
        img = "non-provided"

    pack = {
        "name": name,
        "region": region,
        "address": address,
        "des": des,
        "img": img,
        "url": url,
    }
    print(pack, "\n")
    spots_ls.append(pack)
col.insert_many(spots_ls)
