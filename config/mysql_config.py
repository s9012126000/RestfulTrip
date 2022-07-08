from pymysqlpool.pool import Pool
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pymysql import cursors
import pymysql
import os
load_dotenv()

sql_host = os.getenv('sql_host')
sql_user = os.getenv('sql_user')
sql_pw = os.getenv('sql_passwd')
sql_db = os.getenv('sql_database')

pool = Pool(
    host=sql_host,
    user=sql_user,
    password=sql_pw,
    db=sql_db,
    max_size=10,
    cursorclass=pymysql.cursors.DictCursor
)
pool.init()

engine = create_engine(
    f"mysql+pymysql://{sql_user}:{sql_pw}@{sql_host}:3306/{sql_db}?charset=utf8",
    max_overflow=0,
    pool_size=5,
    pool_timeout=30,
    pool_recycle=-1
)


def sql_strict_insert(table, ls, db):
    keys = list(ls[0].keys())
    columns = ', '.join(keys)
    placeholders = ', '.join(['%s'] * len(ls[0]))
    vals = [tuple(val.values()) for val in ls]
    cursor = db.cursor()
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.executemany(sql, vals)
    db.commit()


def hotels_to_sql(df, db):
    ls = df.to_dict('records')
    keys = list(ls[0].keys())
    columns = ', '.join(keys)
    placeholders = ', '.join(['%s'] * len(ls[0]))
    vals = [tuple(val.values()) for val in ls]
    db.ping(reconnect=True)
    cursor = db.cursor()
    sql = f"""
    INSERT INTO hotels ({columns}) VALUES ({placeholders})
    ON DUPLICATE KEY UPDATE 
        name = VALUES (name), 
        address = VALUES (address), 
        des = VALUES (des), 
        star = VALUES (star)
    """
    cursor.executemany(sql, vals)
    db.commit()


def dt_to_sql(table, ls, db):
    keys = list(ls[0].keys())
    columns = ', '.join(keys)
    placeholders = ', '.join(['%s'] * len(ls[0]))
    vals = [tuple(val.values()) for val in ls]
    db.ping(reconnect=True)
    cursor = db.cursor()
    sql = f"INSERT IGNORE INTO {table} ({columns}) VALUES ({placeholders})"
    cursor.executemany(sql, vals)
    db.commit()


def price_to_sql(ls, db):
    keys = list(ls[0].keys())
    columns = ', '.join(keys)
    placeholders = ', '.join(['%s'] * len(ls[0]))
    vals = [tuple(val.values()) for val in ls]
    db.ping(reconnect=True)
    cursor = db.cursor()
    sql = f"""
    INSERT INTO price ({columns}) VALUES ({placeholders})
    ON DUPLICATE KEY UPDATE price = VALUES (price)
    """
    cursor.executemany(sql, vals)
    db.commit()


def empty_to_sql(dt, db):
    date = tuple(dt['date'])
    if len(date) == 1:
        date = f"('{date[0]}')"
    db.ping(reconnect=True)
    cursor = db.cursor()
    sql = f"""
    UPDATE price 
    SET price = 0
    WHERE date IN {date} AND resource_id = {dt['resource_id']};
    """
    cursor.execute(sql)
    db.commit()