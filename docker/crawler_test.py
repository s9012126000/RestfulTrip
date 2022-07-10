from crawler_config import *

url = 'https://www.booking.com/hotel/tw/cheng-shi-shang-lu-gao-xiong-bo-er-guan.zh-tw.html?aid=304142&label=gen173nr-1DCAso5wFCD3NvdXRoLXNlYS1ob3RlbEgwWARo5wGIAQGYATC4AQfIAQzYAQPoAQH4AQaIAgGoAgO4AoKf3JUGwAIB0gIkYjgxNWQ2ZjgtNmRmNi00OWM3LThlMjQtYzEyNWNlYWNhMzBm2AIE4AIB&sid=f3383f351b4f810b4c8fd5c9f1753eb8&all_sr_blocks=169691402_255146905_0_0_0;checkin=2022-07-30;checkout=2022-07-31;dest_id=-2632378;dest_type=city;dist=0;group_adults=2;group_children=0;hapos=2;highlighted_blocks=169691402_255146905_0_0_0;hpos=2;matching_block_id=169691402_255146905_0_0_0;no_rooms=1;req_adults=2;req_children=0;room1=A%2CA;sb_price_type=total;sr_order=popularity;sr_pri_blocks=169691402_255146905_0_0_0__259700;srepoch=1657436679;srpvid=bb2631c336560081;type=total;ucfs=1&#hotelTmpl'
driver = webdriver.Chrome(ChromeDriverManager(version='104.0.5112.20').install(), options=options)
driver.get(url)
a = driver.find_element(By.TAG_NAME, 'html').text
print(a)