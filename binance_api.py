
import time
import sys
#import win32api
import csv
from binance import Client
from datetime import datetime, timedelta
from sys import platform


def get_api():
    api = []
    with open('real_api.txt', 'r') as file:
        for line in file:
            line = line.split()
            api.append(line[-1])
    return api


API_KEY, API_SECRET = get_api()


#TO_TRADE = 'BTCUSDT'
#TO_TRADE = 'ETHUSDT'
TO_TRADE = 'ADAUSDT'
#QUANTITY = 0.001
#QUANTITY = 0.015
QUANTITY = 18

BTCUSDT = {'to_trade': 'BTCUSDT', 'quantity': 0.001}

#RANGE = 90
RANGE = 30
TOP = 1.0002
#BOT = 0.998
BOT = 0.995

LOGFILE_NAME = TO_TRADE + str(int(time.time())) + '.csv'
UBUNTU_PATH = "/home/ubuntu/TradingBot/"

LOGFILE_NAME = LOGFILE_NAME if platform == "win32" else (UBUNTU_PATH + LOGFILE_NAME)


def safety_stop(client):
    while True:
        try:
            #QUANTITY abfragen bzw alles verkaufen was man hat
            # client.order_market_sell(symbol=TO_TRADE, quantity=QUANTITY)
            sys.exit()
        except:
            continue


class HelpFunctions:
    def __init__(self, client):
        self.client = client

    def get_avg_price(self, error_counter, t):
        t = datetime.fromtimestamp(t)
        threshold = timedelta(seconds=30)
        safety_stop_thr = timedelta(seconds=300)
        try:
            return float(self.client.get_avg_price(symbol=TO_TRADE)['price']), error_counter
        except:
            error_counter[-1][1] += 1 if t - error_counter[-1][0] < threshold else error_counter.append([t, 1])
            time.sleep(1)
            safety_stop(self.client) if t - error_counter[-1][0] > safety_stop_thr else ()
            print(error_counter)
            self.get_avg_price(error_counter, time.time())

    def write_csv(self, to_write, m='a'):
        with open(LOGFILE_NAME, m) as file:
            writer = csv.writer(file, delimiter=';')
            for row in to_write:
                writer.writerow(row)


class TradingBot(HelpFunctions):
    def __init__(self):
        self.client = Client(API_KEY, API_SECRET)
        print(self.client.get_account())

        self.last_prices = [-1.0 for _ in range(RANGE)]
        self.bought_at = 1
        self.price_when_started = float
        self.time_counter = 0

        self.result = 0.0

        #self.error_counter = {'ReadTimeout': [[datetime.fromtimestamp(time.time()), 0]]}

        super().__init__(self.client)

    def trade(self):
        is_bought = False
        self.price_when_started = float(self.client.get_avg_price(symbol=TO_TRADE)['price'])
        print("price when started", self.price_when_started)
        t = datetime.fromtimestamp(time.time())
        to_write = [["Started at", t], ["Price when started: ", str(self.price_when_started).replace('.', ','), "USD"]]
        self.write_csv(to_write, m='w')

        '''synchronize binance server time with locale time'''
        # server_time = int(self.client.get_server_time()['serverTime'] / 1000)
        # gmtime = time.gmtime(server_time)
        # win32api.SetSystemTime(gmtime[0], gmtime[1], 0, gmtime[2], gmtime[3], gmtime[4], gmtime[5], 0)
        # print(self.client.get_account())

        while True:
            t = time.time()

            #act_price, self.error_counter['ReadTimeout'] = self.get_avg_price(self.error_counter['ReadTimeout'], t)
            try:
                act_price = float(self.client.get_avg_price(symbol=TO_TRADE)['price'])
            except:
                print("Exception!", "get_avg_price failed", "bad connection")
                self.write_csv([["Bad Connection"]])
                #time.sleep(2)
                continue

            #try:
            #    act_price = float(self.client.get_avg_price(symbol=TO_TRADE)['price'])
            #except:
            #    self.error_counter['ReadTimeout'] = self.error_counter['ReadTimeout'] + 1
            #    time.sleep(1)
            #    safety_stop(self.client) if self.error_counter['ReadTimeout'] > 300 else ()
            #    continue

            self.last_prices.append(act_price)
            del self.last_prices[0]

            #to_write = [t, act_price]

            if not is_bought:
                change_30 = self.last_prices[-1] / self.last_prices[0]
                if change_30 > 1.0:
                    print("BUY!!!")
                    # order = self.client.order_market_buy(symbol=TO_TRADE, quantity=QUANTITY)
                    # print(order)
                    is_bought = True
                    self.bought_at = act_price
                    #to_write.append("BUY!!!")

                    print(datetime.fromtimestamp(t) + timedelta(hours=2))
                    print(self.bought_at)
                    print(change_30)
                    to_write = [[datetime.fromtimestamp(t) + timedelta(hours=2), str(self.bought_at).replace('.', ','),
                                 "BUY"]]
                    self.write_csv(to_write)

            if is_bought:
                change = act_price / self.bought_at
                if change > TOP or change < BOT:
                    print("SELL!!")
                    # order = self.client.order_market_sell(symbol=TO_TRADE, quantity=QUANTITY)
                    # print(order)
                    is_bought = False
                    self.result += (act_price - self.bought_at) * QUANTITY
                    #to_write.append("SELL!!!")

                    print(datetime.fromtimestamp(t) + timedelta(hours=2))
                    print(self.bought_at)
                    print(change)
                    print("RESULT", self.result)
                    to_write = [[datetime.fromtimestamp(t) + timedelta(hours=2), str(self.bought_at).replace('.', ','),
                                 str(change).replace('.', ','), "SELL"], ["RESULT", self.result, "€"]]
                    self.write_csv(to_write)

            self.time_counter += 1
            time.sleep(0.75)
            t_end = time.time()
            #print(t_end - t)



def main():
    trading_bot = TradingBot()
    trading_bot.trade()


main()
