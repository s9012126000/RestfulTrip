from config.mysql_config import *
import pandas as pd
import re
MyDb = pool.get_conn()
MyDb.ping(reconnect=True)
cursor = MyDb.cursor()

cursor.execute("SELECT resource, url FROM resources")
urls = cursor.fetchall()
pat = re.compile('https[\S]+\?')
al = [re.match(pat, x['url']).group() for x in urls]

hotel = [(re.match(pat, x['url']).group(), 1) for x in urls if x['resource'] == 1]
booking = [(re.match(pat, x['url']).group(), 1) for x in urls if x['resource'] == 2]
agoda = [(re.match(pat, x['url']).group(), 1) for x in urls if x['resource'] == 3]

h = pd.DataFrame(hotel, columns=['url', 'count'])
b = pd.DataFrame(booking, columns=['url', 'count'])
a = pd.DataFrame(agoda, columns=['url', 'count'])

h = h.groupby('url').sum().reset_index()
h = h[h['count'] > 1]
h_err = len(h)

b = b.groupby('url').sum().reset_index()
b = b[b['count'] > 1]
b_err = len(b)

a = a.groupby('url').sum().reset_index()
a = a[a['count'] > 1]
a_err = len(a)