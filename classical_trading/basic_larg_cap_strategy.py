
import json
import requests
import time as tm
import numpy as np
import tabulate as tb

import bitfinex as bt
import bitfinex_web_socket_auth as bwsa

from matplotlib import pyplot as plt
import pyti.simple_moving_average as sma

import bitfinex as btx

ONE_PRECISION_POINT = 0.0001
SIDE_PRICE_DIFF_DICT = {'ask': -1, 'bid': 1}

class BasicLargeCapStrategy(object):
    def __init__(self, symbols, dollar_amount):
        self.bitfinex_websocket_client = bwsa.get_authenticated_client()
        self.symbols = symbols
        self.dollar_amount = dollar_amount
        self.orders_dict = {}

    def get_historical_data(self, limit, symbol):
        ''' MTS, OPEN, CLOSE, HIGH, LOW, VOLUME '''
        try:
            hist_data = json.loads(requests.get('https://api-pub.bitfinex.com/v2/candles/trade:1m:{0}/hist?limit={1}'.format(symbol, limit)).text)
            hist_data.reverse()
            return np.array(hist_data)
        except Exception as e:
            import pdb; pdb.set_trace()
            print(e)

    def ticker(self, symbol):
        try:
            tick_data = json.loads(requests.get('https://api-pub.bitfinex.com/v2/ticker/{0}'.format(symbol)).text)
            return {'ask': tick_data[2], 'bid':tick_data[0], 'high':tick_data[8], 'low':tick_data[9]}
        except Exception as e:
            import pdb; pdb.set_trace()
            print(e)

    def find_graph_collision(self, data, data_sma):
        collision_points = []
        for i in range(1, len(data)):
            if data[i-1] > data_sma[i-1] and data[i] < data_sma[i]:
                collision_points.append(i)
            if data[i-1] < data_sma[i-1] and data[i] > data_sma[i]:
                collision_points.append(i)
        return collision_points

    def get_sma_trading_condition_from_data(self, data, data_sma):
        if data[-1] > data_sma[-1] and data[-2] < data_sma[-2]:
            return 'sma_above_below - buy'
        if data[-1] < data_sma[-1] and data[-2] > data_sma[-2]:
            return 'sma_below_above - sell'
        return 'stable'

    def get_sma_trading_condition(self, symbol):
        data = self.get_historical_data(1400, symbol)
        data = data[:, 2]
        data_sma = sma.simple_moving_average(data, 100)[100:]
        data = data[100:]
        trading_condition = self.get_sma_trading_condition_from_data(data, data_sma)
        return trading_condition

    def check_trading_condition(self):
        trade_condition_symbols = []
        for symbol in self.symbols:
            trading_condition = self.get_sma_trading_condition(symbol)
            if not trading_condition == 'stable':
                trade_condition_symbols.append((symbol, trading_condition))
        return trade_condition_symbols

    def start_strategy_routine(self):
        profit_req = 1.004
        actual_symbol = ''
        is_free = True
        while True:
            tm.sleep(10.0)
            trade_condition_symbols = self.check_trading_condition()
            print(trade_condition_symbols)
            if len(self.orders_dict) > 0:
                print('a')
                order_id_buy, order_id_sell = self.orders_dict[actual_symbol]
                ask_order_finished = abs(self.bitfinex_websocket_client.active_orders[order_id_buy].amount) < 0.0000001
                bid_order_finished = abs(self.bitfinex_websocket_client.active_orders[order_id_sell].amount) < 0.0000001
                print(self.bitfinex_websocket_client.active_orders[order_id_buy].amount)
                print(self.bitfinex_websocket_client.active_orders[order_id_sell].amount)
                print('b')
                if ask_order_finished and bid_order_finished:
                    print('c')
                    is_free = True
                else:
                    print('d')
                    is_free = False
            print('is_free: {0}'.format(is_free))
            if not trade_condition_symbols == [] and is_free:
                symbol = trade_condition_symbols[0][0]
                trading_condition = trade_condition_symbols[0][1]
                price_dict = self.ticker(symbol)
                price = (price_dict['ask'] + price_dict['bid']) / 2
                amount = self.dollar_amount / price
                if price_dict['high'] * 0.99 > price and price_dict['low'] * 1.01 < price:                
                    print(trading_condition)
                    if not trading_condition == 'stable':
                        if trading_condition == 'sma_above_below - buy':
                            is_successful, order_id_buy = self.bitfinex_websocket_client.place_new_order(symbol, amount, price_dict['ask'])
                            is_successful, order_id_sell = self.bitfinex_websocket_client.place_new_order(symbol, -amount, price_dict['ask'] * profit_req)
                            print('order issued')
                            self.orders_dict[symbol] = [order_id_buy, order_id_sell]
                            print(self.orders_dict)
                            actual_symbol = symbol
                        if trading_condition == 'sma_above_below - sell':
                            is_successful, order_id_sell = self.bitfinex_websocket_client.place_new_order(symbol, -amount, price_dict['bid'])
                            is_successful, order_id_buy = self.bitfinex_websocket_client.place_new_order(symbol, amount, price_dict['bid'] / profit_req)
                            print('order issued')
                            self.orders_dict[symbol] = [order_id_buy, order_id_sell]
                            print(self.orders_dict)
                            actual_symbol = symbol
