import pymysql
from pymysql.cursors import DictCursor

def get_db():
    return pymysql.connect(
        host="localhost",  # MySQL tetap lokal
        port=3306,
        user="root",
        password="",
        database="monitoring_produk_eeng",
        cursorclass=DictCursor
    )
