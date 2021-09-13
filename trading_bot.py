import time
import csv
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
RANGE = 60  # how much time to look back
TOP = 1.0002  # good case
BOT = 0.995  # bad case, sell

'''Logfile path'''
NAME = TO_TRADE + str(int(time.time())) + '.csv'  # what to trade and start time
UBUNTU_PATH = "/home/ubuntu/TradingBot/"  # path on the aws server

LOGFILE_NAME = NAME if platform == "win32" else UBUNTU_PATH + NAME  # actual logfile path


class HelpFunctions:
    def __init__(self, client):
        self.client = client

    '''give back the current margin price, float'''
    def get_price(self) -> float:
        try:
            return float(self.client.get_margin_price_index(symbol=TO_TRADE)['price'])
        except:
            self.write_csv([["Bad Connection"]])
            self.get_price()

    '''write csv logfile and save it to logfile name'''
    def write_csv(self, to_write, m='a'):
        with open(LOGFILE_NAME, m) as file:
            writer = csv.writer(file, delimiter=';')
            for row in to_write:
                writer.writerow(row)


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

    def start(self):
        is_bought = False  # give back the current state
        self.price_when_started = self.get_price()  # get current price in float
        delta = 1.0  # time delta how long to wait

        '''create logfile'''
        to_write = [["Started at", datetime.fromtimestamp(time.time())],
                    ["Price when started: ", str(self.price_when_started).replace('.', ','), "USD"]]
        self.write_csv(to_write, m='w')

        '''main loop'''
        while True:
            curr_price = self.get_price()  # get current price
            t = time.time()  # get time, float

            '''add current price to list and delete the oldest one'''
            self.last_prices.append(curr_price)
            del self.last_prices[0]

            # only temp
            time.sleep(0.2)

            '''first state: nothing is bought'''
            if not is_bought:
                pass

            '''second state: crypto is bought'''
            if is_bought:
                pass

            '''calculate time to wait, should be 1 second for one loop'''
            wait = 1.0 - delta
            time.sleep(wait)
            t_end = time.time()
            delta = t_end - t
            print(delta)


if __name__ == '__main__':
    trading_bot = TradingBot()
    trading_bot.start()
