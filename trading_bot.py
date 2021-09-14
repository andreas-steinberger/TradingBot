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

FAKE_ORDER = {'fills': [{'price': 100}]}

'''Settings'''
RANGE = 30  # 30  # how much time to look back
TOP = 1.0002  # good case
BOT = 0.995  # bad case, sell
TRADING_FEE = 0.00075  # trading fee per transaction

'''Logfile path'''
_NAME = "Logfile.db"  # what to trade and start time
_UBUNTU_PATH = "/home/ubuntu/TradingBot/"  # path on the aws server

LOGFILE_NAME = _NAME if platform == "win32" else _UBUNTU_PATH + _NAME  # actual logfile path


'''help to build the sql database string'''
def f(content):
    string = ""
    for cont in content:
        try:
            float(cont)
            s = str(cont)
        except ValueError:
            s = f"\'{cont}\'"

        s = s.replace(" ", "_")
        s = s.replace(":", "-")
        string += s + ', '

    string = string[:-2]
    return string


'''get a time delta to a readable string'''
def f2(time_delta):
    t = time_delta / 60
    if t < 1:
        return str(round(time_delta, 1)) + 's'
    else:
        min = int(t)
        s = int((t - min) * 60)
        return f"{min}min, {s}s"


class SQL:
    '''SQL database for logfiles, after creating only 'insert_data()' is needed'''

    DEFAULT = "INSERT INTO <table_name> VALUES"
    TABLE = "CREATE TABLE <table_name>"

    def __init__(self):
        self.conn = sqlite3.connect(LOGFILE_NAME)
        self.table_name = TO_TRADE + str(int(time.time()))
        self.create_table()

    def create_table(self):
        content = "Timestamp text, Symbol text, Quantity real, Bought_at real, Sold_at real, Difference real," \
                  "Profit real, Time_bought text, Time_hold text, Total_fee real, Total_profit real, Started_at real"
        self.insert_data(content, self.TABLE)

    def insert_data(self, content, mode=DEFAULT):
        c = self.conn.cursor()

        string = content
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
            print("Bad Connection, place order")
            return False

    '''give back the current margin price, float'''
    def get_price(self) -> float:
        try:
            return float(self.client.get_margin_price_index(symbol=TO_TRADE)['price'])
        except:
            print("Bad Connection, get price")
            self.get_price()


class TradingBot(HelpFunctions):
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        print(self.get_price(), 'USD')  # to see if it's working

        self.last_prices = [-1.0 for _ in range(RANGE)]  # keep the prices from the last seconds
        self.price_when_started = float  # price when started the client

        self.result = 0.0
        self.fee_total = 0.0

        # create instance of HelpingFunctions
        super().__init__(self.client)

        # create instance of SQL to write logfiles
        self.s = SQL()

    # for testing
    def fake_order(self):
        price = self.get_price()
        return {'fills': [{'price': price}]}

    # run
    def start(self):
        is_bought = False  # give back the current state
        self.price_when_started = self.get_price()  # get current price in float

        # price when bought, current price to calculate
        bought_at, price_to_compare, time_bought = float, float, float

        '''create logfile'''
        to_write = f([str(datetime.fromtimestamp(time.time())), TO_TRADE, QUANTITY, "", "", "", "", "", "", "", "",
                      self.price_when_started])
        self.s.insert_data(to_write)

        '''main loop'''
        while True:
            t = time.time()  # time at the beginning of the loop, float
            curr_price = self.get_price()  # get current price

            '''add current price to list and delete the oldest one'''
            self.last_prices.append(curr_price)
            del self.last_prices[0]

            '''first state: nothing is bought'''
            if not is_bought:  # buy
                change = self.last_prices[-1] / self.last_prices[0]  # percent, e.g. 0.998, 1.002
                if change > 1.0:
                    '''Attention, next line is ordering with real money!'''
                    # order = self.place_order('buy', t)
                    order = self.fake_order()
                    if not isinstance(order, bool):
                        print("bought at ", datetime.fromtimestamp(t))
                        is_bought = True
                        price_to_compare = float(order['fills'][0]['price'])

                        # for logging
                        bought_at = price_to_compare
                        print(bought_at)
                        time_bought = t

            '''second state: crypto is bought'''
            if is_bought:
                change = curr_price / price_to_compare  # percent, e.g. 0.998, 1.002
                print(change, curr_price, price_to_compare)
                if change > TOP:
                    price_to_compare = price_to_compare * change  # update the price to calculate
                    print(change)
                    print(price_to_compare)

                elif change < BOT:  # sell
                    '''Attention, next line is ordering with real money!'''
                    # order = self.place_order('sell', t)
                    order = self.fake_order()
                    if not isinstance(order, bool):
                        print("sold at", datetime.fromtimestamp(t))
                        is_bought = False

                        # for logging
                        sold_at = float(order['fills'][0]['price'])
                        print(sold_at)
                        fee = (bought_at + sold_at) * TRADING_FEE * QUANTITY
                        change_percent = sold_at / bought_at - TRADING_FEE
                        time_hold = t - time_bought
                        profit = (sold_at - bought_at) * QUANTITY - fee
                        self.result += profit
                        self.fee_total += fee

                        # writing logfile
                        to_write = f([str(datetime.fromtimestamp(t)), TO_TRADE, QUANTITY, bought_at, sold_at,
                                      change_percent, profit, str(datetime.fromtimestamp(time_bought)), f2(time_hold),
                                      self.fee_total, self.result, ""])
                        self.s.insert_data(to_write)

            '''calculate time to wait, should be 1 second for one loop'''
            t_end = time.time()  # time at the and of the loop, float
            wait = 0.99 - (t_end - t)
            if wait > 0.0:
                time.sleep(wait)
            # duration = time.time() - t  # complete time with waiting time
            # print("Duration", duration)


if __name__ == '__main__':
    trading_bot = TradingBot()
    trading_bot.start()
