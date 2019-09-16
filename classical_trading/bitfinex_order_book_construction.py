
import sys
import time as tm

import pickle as pk
import websocket as wbs

import json
import threading
import time

import os
import tabulate as tb

NUM_OF_PRICE_POINTS = 25
HEART_BEAT = 'hb'

class WebSocketOrderBook(object):
    def __init__(self, raw_socket_data):
        self.ask, self.bid = [], []
        self.is_book_initialized = False
        self.process_raw_data(json.loads(raw_socket_data))

    def get_ask_price(self):
        return self.ask[0][0]

    def get_bid_price(self):
        return self.bid[0][0]

    def process_raw_data(self, raw_socket_data):
        self.ask = raw_socket_data[1][NUM_OF_PRICE_POINTS:]
        self.bid = raw_socket_data[1][:NUM_OF_PRICE_POINTS]
        if len(self.ask) == NUM_OF_PRICE_POINTS and len(self.bid) == NUM_OF_PRICE_POINTS:
            self.is_book_initialized = True
        else:
            raise Exception('Wrong book size.')
        if any([a[-1] > 0 for a in self.ask]):
            raise Exception('Wrong ask amount direction.')
        if any([b[-1] < 0 for b in self.bid]):
            raise Exception('Wrong bid amount direction.')

    def add_update_asks(self, price, count, amount):
        price_exists = False
        for i in range(len(self.ask)):
            if self.ask[i][0] == price:
                price_exists = True
                price_count = i
                break
        if price_exists:
            self.ask[price_count] = [price, count, amount]
        else:
            self.ask.append([price, count, amount])
        self.ask.sort(key=lambda k: k[0])
        self.ask = self.ask[:NUM_OF_PRICE_POINTS]

    def add_update_bids(self, price, count, amount):
        price_exists = False
        for i in range(len(self.bid)):
            if self.bid[i][0] == price:
                price_exists = True
                price_count = i
                break
        if price_exists:
            self.bid[price_count] = [price, count, amount]
        else:
            self.bid.append([price, count, amount])
        self.bid.sort(key=lambda k: -k[0])
        self.bid = self.bid[:NUM_OF_PRICE_POINTS]

    def delete_price_level_asks(self, price):
        for i in range(len(self.ask)):
            if self.ask[i][0] == price:
                price_exists = True
                price_count = i
        if price_exists:
            self.ask.pop(price_count)
        else:
            raise Exception('Wrong removal')

    def delete_price_level_bids(self, price):
        for i in range(len(self.bid)):
            if self.bid[i][0] == price:
                price_exists = True
                price_count = i
        if price_exists:
            self.bid.pop(price_count)
        else:
            raise Exception('Wrong removal')

    def update_book(self, update):
        if HEART_BEAT in update:
            return
        price, count, amount = update[1]
        if count > 0:
            if amount < 0:
                self.add_update_asks(price, count, amount)
            if amount > 0:
                self.add_update_bids(price, count, amount)
        elif count == 0:
            if amount == 1:
                self.delete_price_level_bids(price)
            elif amount == -1:
                self.delete_price_level_asks(price)
            else:
                raise Exception('Wrong amount')
        else:
            raise Exception('Wrong count')

class WebSocketThread(threading.Thread):
    def __init__(self, symbol):
        threading.Thread.__init__(self)
        self.res_list = []
        self.ws = wbs.WebSocketApp('wss://api-pub.bitfinex.com/ws/2')
        self.ws.on_open = lambda s: s.send\
            ('{ "event": "subscribe", "channel": "book", "symbol": "'+symbol+'"}')
        self.ws.on_message = lambda s, evt:  self.res_list.append(evt)
    def get_next_update(self):
        if len(self.res_list) > 0:
            return self.res_list.pop(0)
    def wait_for_next_update(self):
        while not len(self.res_list) > 0:
            pass
        return self.get_next_update()
    def get_update_by_index(self, index):
        if len(self.res_list) > index:
            for i in range(index):
                r = self.res_list.pop(0)
        return self.res_list.pop(0)
    def get_stack_length(self):
        return len(self.res_list)
    def wait_for_capacity(self, length):
        while not len(self.res_list) >= length:
            pass
        return None
    def close_thread(self):
       self.ws.keep_running = False
    def run(self):
       self.ws.run_forever()

class OrderBookThread(threading.Thread):
    def __init__(self, symbol):
        threading.Thread.__init__(self)
        self.wst = WebSocketThread(symbol)
        self.wst.start()
        self.wst.wait_for_capacity(3)
        raw_socket_data = self.wst.get_update_by_index(2)
        self.wsob = WebSocketOrderBook(raw_socket_data)
        self.keep_running = True
        self.is_stopped = False

    def close_thread(self):
        self.keep_running = False
        while not self.is_stopped:
            pass

    def run(self):
        while self.keep_running:
            resp = self.wst.wait_for_next_update()
            self.wsob.update_book(json.loads(resp))
        self.wst.close_thread()
        self.is_stopped = True

def print_order_book(ob):
    print(tb.tabulate([[a,b] for (a, b) in zip(ob.ask, ob.bid)], headers=['Ask', 'Bid']))

def main():
    obt = OrderBookThread(sys.argv[1])
    obt.start()
    while True:
        os.system('clear')
        print_order_book(obt.wsob)
        tm.sleep(0.01)

if __name__ == '__main__':
    main()
