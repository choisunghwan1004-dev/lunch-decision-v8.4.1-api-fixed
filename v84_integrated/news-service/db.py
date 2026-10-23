import os
from contextlib import contextmanager
from dotenv import load_dotenv
load_dotenv()
@contextmanager
def db():
 import pymysql
 conn=pymysql.connect(host=os.getenv('NEWS_DB_HOST','127.0.0.1'),port=int(os.getenv('NEWS_DB_PORT','3306')),user=os.getenv('NEWS_DB_USER','root'),password=os.getenv('NEWS_DB_PASSWORD',''),database=os.getenv('NEWS_DB_NAME','lunch_decision_v83'),charset='utf8mb4',cursorclass=pymysql.cursors.DictCursor,autocommit=False)
 try:
  with conn.cursor() as cur:yield cur
  conn.commit()
 except:conn.rollback();raise
 finally:conn.close()
def read(sql,args=()):
 with db() as c:c.execute(sql,args);return c.fetchall()
