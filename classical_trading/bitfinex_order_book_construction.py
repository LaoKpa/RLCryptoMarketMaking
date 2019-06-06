
import sys
import time

import pickle as pk
import websocket as wbs

import json
import threading
import time

NUM_OF_PRICE_POINTS = 25

class WebSocketOrderBook(object):
    def __init__(self, raw_socket_data):
        self.ask, self.bid = [], []
        self.process_raw_data(json.loads(raw_socket_data))

    def process_raw_data(self, raw_socket_data):
        self.ask = raw_socket_data[1][NUM_OF_PRICE_POINTS:]
        self.bid = raw_socket_data[1][:NUM_OF_PRICE_POINTS]
        if any([a[-1] > 0 for a in self.ask]):
            raise Exception('Wrong ask amount direction.')
        if any([b[-1] < 0 for b in self.bid]):
            raise Exception('Wrong bid amount direction.')

    def add_update_asks(self, price, count, amount):
        for i in range(len(self.ask)):
            if self.ask[i][0] == price:
                price_exists = True
                price_count = i
        if price_exists:
            self.ask[i] = [price, count, amount]
        else:
            self.ask.append([price, count, amount])
        self.ask.sort(key=lambda k: k[0])
        self.ask = self.ask[:NUM_OF_PRICE_POINTS]

    def add_update_bids(self, price, count, amount):
        for i in range(len(self.bid)):
            if self.bid[i][0] == price:
                price_exists = True
                price_count = i
        if price_exists:
            self.bid[i] = [price, count, amount]
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
    def __init__(self):
        threading.Thread.__init__(self)
        self.res_list = []
        self.ws = wbs.WebSocketApp('wss://api-pub.bitfinex.com/ws/2')
        self.ws.on_open = lambda s: s.send('{ "event": "subscribe", "channel": "book", "symbol": "tBTCUSD"}')
        self.ws.on_message = lambda s, evt:  self.res_list.append(evt)
    def get_next_update(self):
        if len(self.res_list) > 0:
            return self.res_list.pop(0)
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
    def run(self):
       self.ws.run_forever()

def main():
    wst = WebSocketThread()
    wst.start()
    wst.wait_for_capacity(3)
    raw_socket_data = wst.get_update_by_index(2)
    wsob = WebSocketOrderBook(raw_socket_data)
    while True:
        wsob.update_book(json.loads(wst.get_next_update()))

if __name__ == '__main__':
    main()
