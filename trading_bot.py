import time
import sqlite3
from binance import Client
from datetime import datetime
from sys import platform  # get platform, windows or ubuntu


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

'''Crypto currencies: Bitcoin, Ethereum, ADA'''
CRYPTO = [('BTCUSDT', 0.001), ('ETHUSDT', 0.015), ('ADAUSDT', 18)]
TO_TRADE = CRYPTO[0][0]
QUANTITY = CRYPTO[0][1]

'''Settings'''
RANGE = 10  # 30  # how much time to look back
TOP = 1.0002  # good case
BOT = 0.995  # bad case, sell

'''Logfile path'''
_NAME = "Logfile.db"  # what to trade and start time
_UBUNTU_PATH = "/home/ubuntu/TradingBot/"  # path on the aws server

LOGFILE_NAME = _NAME if platform == "win32" else _UBUNTU_PATH + _NAME  # actual logfile path


class SQL:
    '''SQL database for logfiles, after creating only 'insert_data()' is needed'''
    def __init__(self):
        self.conn = sqlite3.connect(LOGFILE_NAME)
        self.table_name = TO_TRADE + str(int(time.time()))
        self.create_table()

    def create_table(self):
        content = "Timestamp text, Symbol text, Quantity real, Price real"
        mode = f"CREATE TABLE {self.table_name}"
        self.insert_data(content, mode)

    def insert_data(self, content, mode=f"INSERT INTO <table_name> VALUES"):
        c = self.conn.cursor()

        string = str(content)
        mode = mode.replace("<table_name>", self.table_name)
        c.execute(f"{mode}({string})")  # string = "abc", "def", 100, 10.5

        self.conn.commit()


class HelpFunctions:
    def __init__(self, client):
        self.client = client

    '''description'''
    def place_order(self, mode, t):
        try:
            if mode == 'buy':
                return self.client.order_market_buy(symbol=TO_TRADE, quantity=QUANTITY)
            elif mode == 'sell':
                return self.client.order_market_sell(symbol=TO_TRADE, quantity=QUANTITY)
        except:
            # self.write_csv([["Bad Connection, place order"]])
            return False

    '''give back the current margin price, float'''
    def get_price(self) -> float:
        try:
            return float(self.client.get_margin_price_index(symbol=TO_TRADE)['price'])
        except:
            # self.write_csv([["Bad Connection, get price"]])
            self.get_price()


class TradingBot(HelpFunctions):
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        print(self.get_price(), 'USD')  # to see if it's working

        self.last_prices = [-1.0 for _ in range(RANGE)]  # keep the prices from the last seconds
        self.bought_at = 1  # price when bought
        self.price_when_started = float  # price when started the client
        self.price_to_sell_at = self.bought_at  # price when to sell in the bad case

        self.result = 0.0

        # create instance of HelpingFunctions
        super().__init__(self.client)

        # create instance of SQL to write logfiles
        self.s = SQL()

    def start(self):
        is_bought = False  # give back the current state
        self.price_when_started = self.get_price()  # get current price in float

        '''create logfile'''
        # to_write = [["Started at", datetime.fromtimestamp(time.time())],
        #            ["Price when started: ", str(self.price_when_started).replace('.', ','), "USD"]]
        # self.write_csv(to_write, m='w')

        '''main loop'''
        while True:
            t = time.time()  # time at the beginning of the loop, float
            curr_price = self.get_price()  # get current price

            '''add current price to list and delete the oldest one'''
            self.last_prices.append(curr_price)
            del self.last_prices[0]

            '''first state: nothing is bought'''
            if not is_bought:
                change = self.last_prices[-1] / self.last_prices[0]  # percent, e.g. 0.998, 1.002
                print(change)
                if change > 1.0:
                    order = self.place_order('buy', t)
                    if order:
                        is_bought = True
                        self.bought_at = float(order['fills'][0]['price'])

                    # to_write = [["to write"]]
                    # self.write_csv(to_write)

            '''second state: crypto is bought'''
            if is_bought:
                pass

            '''calculate time to wait, should be 1 second for one loop'''
            t_end = time.time()  # time at the and of the loop, float
            wait = 0.99 - (t_end - t)
            if wait > 0.0:
                time.sleep(wait)
            # duration = time.time() - t  # complete time with waiting time


if __name__ == '__main__':
    trading_bot = TradingBot()
    trading_bot.start()
