from config.crawler_config import *
import json
URL_LOC = "https://zh.wikipedia.org/wiki/中華民國臺灣地區鄉鎮市區列表"


def get_divisions():
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.delete_all_cookies()
    driver.get(URL_LOC)
    div = driver.find_elements(
        By.XPATH, "//div[@id='mw-content-text']/div[1]/table[7]/tbody/tr/td[1]/small"
    )
    divs = set([x.text for x in div])
    driver.quit()
    return divs


divisions = get_divisions()
divisions = [div.replace("臺", "台") if "臺" in div else div for div in divisions]
with open("jsons/divisions.json", "w") as f:
    json.dump(list(divisions), f)
