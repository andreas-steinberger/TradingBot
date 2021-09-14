import sqlite3
import time
from binance import Client
from sys import platform

'''get api from text file'''
def get_api():
    api = []
    with open('real_api.txt', 'r') as file:
        for line in file:
            line = line.split()
            api.append(line[-1])
    return api


'''API Key and API Secret'''
API_KEY, API_SECRET = get_api()

DATABASE_PATH = "CollectData.db" if platform == "win32" else "/home/ubuntu/TradingBot/CollectData.db"


class CollectData:
    _insert = "INSERT INTO prices VALUES"
    _table = "CREATE TABLE prices"

    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        self.conn = sqlite3.connect(DATABASE_PATH)
        self.make_sql("price real", self._table)

    def make_sql(self, content, mode=_insert):
        c = self.conn.cursor()
        c.execute(f"{mode}({content})")
        self.conn.commit()

    def get_price(self) -> float:
        try:
            return float(self.client.get_margin_price_index(symbol='BTCUSDT')['price'])
        except:
            print("Bad Connection, get price")
            self.get_price()

    def collect(self):

        while True:
            t_start = time.time()

            price = self.get_price()
            self.make_sql(price)

            t_end = time.time()
            wait = 0.99 - (t_end - t_start)
            if wait > 0.0:
                time.sleep(wait)

            # print(time.time() - t_start)


cd = CollectData()
cd.collect()
