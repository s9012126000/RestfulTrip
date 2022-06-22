from pymysqlpool.pool import Pool
from dotenv import load_dotenv
from pymysql import cursors
import pymysql
import os
load_dotenv()


pool = Pool(
    host=os.getenv('host'),
    user=os.getenv('user'),
    password=os.getenv('passwd'),
    db=os.getenv('database'),
    cursorclass=pymysql.cursors.DictCursor
)
pool.init()
MyDb = pool.get_conn()


def sql_bulk(table, ls):
    keys = list(ls[0].keys())
    columns = ', '.join(keys)
    placeholders = ', '.join(['%s'] * len(ls[0]))
    vals = [tuple(val.values()) for val in ls]
    cursor = MyDb.cursor()
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.executemany(sql, vals)
    MyDb.commit()

