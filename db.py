# db.py
import pymysql
from pymysql.cursors import DictCursor
import os

def get_db():
    return pymysql.connect(
        host=os.environ.get("MYSQL_HOST", "localhost"),
        port=int(os.environ.get("MYSQL_PORT", 3306)),
        user=os.environ.get("MYSQL_USER", "root"),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        database=os.environ.get("MYSQL_DATABASE", "monitoring_produk_eeng"),
        cursorclass=DictCursor
    )
