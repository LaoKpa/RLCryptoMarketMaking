
import json
import requests
import time as tm
import numpy as np
import tabulate as tb

import bitfinex as bt
# import bitfinex_web_socket_auth as bwsa

from matplotlib import pyplot as plt

ONE_PRECISION_POINT = 0.0001
SIDE_PRICE_DIFF_DICT = {'ask': -1, 'bid': 1}

while True:
    print('duck')

def get_historical_data(symbol, limit):
    try:
        hist_data = json.loads(requests.get('https://api-pub.bitfinex.com/v2/candles/trade:1m:{0}/hist?limit={1}'.format(symbol, limit)).text)
        hist_data.reverse()
        return np.array(hist_data)
    except Exception as e:
        import pdb; pdb.set_trace()
        print(e)

class BasicLargeCapStrategy(object):
    def __init__(self, symbol, req_spread_percntage, dollar_amount):
        self.order_book.start()
        self.bitfinex_websocket_client = bwsa.get_authenticated_client()
        self.req_spread_percntage = req_spread_percntage
        self.symbol = symbol 
        self.low_case_symbol = self.symbol[1:].lower()
        self.order_id_dictionary = {}
        self.dollar_amount = dollar_amount
        if not self.order_book.wsob.is_book_initialized:
            raise Exception('Order book did not initialized correctly.') 

    def initiate_order(self, amount, side):
        current_price_dict = self.get_current_price_dict()
        alteration =  ONE_PRECISION_POINT * SIDE_PRICE_DIFF_DICT[side]
        amount = SIDE_PRICE_DIFF_DICT[side] * amount
        is_successful, order_id = self.bitfinex_websocket_client.place_new_order(self.symbol, amount, current_price_dict[side] + alteration)
        if is_successful:
            self.order_id_dictionary[side] = order_id
        else:
            raise Exception('Unsuccessful order placement.')
        return order_id

    def get_current_price_dict(self):
        return {'ask':self.order_book.wsob.get_ask_price(), 'bid':self.order_book.wsob.get_bid_price()}

    def get_current_book_dict(self):
        return {'ask':self.order_book.wsob.ask.copy(), 'bid':self.order_book.wsob.bid.copy()}

    def update_order(self, order_id, amount, price, side):
        amount = SIDE_PRICE_DIFF_DICT[side] * amount
        if not self.bitfinex_websocket_client.update_order(order_id, amount, price):
            raise Exception('Unsuccessful order update.')

    def get_current_price(self, side):
        price_index = 0
        first_in_line_precedence = 0
        second_in_line_precedence = 1
        precedenes, count = self.get_order_book_precedenes(side)
        current_book_dict = self.get_current_book_dict()
        current_book_dict = current_book_dict[side]
        if precedenes == 0 and count == 1:
            return current_book_dict[second_in_line_precedence][price_index]
        else:
            return current_book_dict[first_in_line_precedence][price_index]

    def start_strategy_routine(self):
        price_dict = self.get_current_price_dict()
        price = (price_dict['ask'] + price_dict['bid']) / 2
        amount = self.dollar_amount / price
        order_id_ask = self.initiate_order(amount, 'ask')
        order_id_bid = self.initiate_order(amount, 'bid')
        s_t = self.req_spread_percntage * price
        r_t = s_t * amount
        while True:
            tm.sleep(0.1)
            p_a_h = self.get_current_price('ask')
            p_b_h = self.get_current_price('bid')
            p_a_e = self.bitfinex_websocket_client.active_orders[order_id_ask].exec_price
            p_b_e = self.bitfinex_websocket_client.active_orders[order_id_bid].exec_price
            a_e_a = self.bitfinex_websocket_client.active_orders[order_id_ask].exec_amount
            a_e_b = self.bitfinex_websocket_client.active_orders[order_id_bid].exec_amount
            order_update_dict = self.pricing_model.get_updated_order_prices(s_t, r_t, p_a_h, p_b_h, p_a_e, p_b_e, abs(a_e_a), abs(a_e_b))
            ask_order_finished = self.bitfinex_websocket_client.active_orders[order_id_ask].amount == 0
            bid_order_finished = self.bitfinex_websocket_client.active_orders[order_id_bid].amount == 0
            if not ask_order_finished:
                self.update_order(order_id_ask, order_update_dict['ask']['amount'], order_update_dict['ask']['price'], 'ask')
            if not bid_order_finished:
                self.update_order(order_id_bid, order_update_dict['bid']['amount'], order_update_dict['bid']['price'], 'bid')
            if ask_order_finished and bid_order_finished:
                return True
