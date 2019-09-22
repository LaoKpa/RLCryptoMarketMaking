
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


def get_historical_data(symbol, limit):
    ''' MTS, OPEN, CLOSE, HIGH, LOW, VOLUME '''
    try:
        hist_data = json.loads(requests.get('https://api-pub.bitfinex.com/v2/candles/trade:1m:{0}/hist?limit={1}'.format(symbol, limit)).text)
        hist_data.reverse()
        return np.array(hist_data)
    except Exception as e:
        import pdb; pdb.set_trace()
        print(e)

def find_graph_collision(self, data, data_sma):
    collision_points = []
    for i in range(1, len(data)):
        if data[i-1] > data_sma[i-1] and data[i] < data_sma[i]:
            collision_points.append((i,'sma: low->high'))
        if data[i-1] < data_sma[i-1] and data[i] > data_sma[i]:
            collision_points.append((i,'sma: high->low'))
    return collision_points

class BasicLargeCapStrategy(object):
    def __init__(self, symbol, dollar_amount):
        self.bitfinex_websocket_client = bwsa.get_authenticated_client()
        self.symbol = symbol
        self.low_case_symbol = self.symbol[1:].lower()
        self.order_id_dictionary = {}
        self.dollar_amount = dollar_amount

    def get_historical_data(self, limit):
        ''' MTS, OPEN, CLOSE, HIGH, LOW, VOLUME '''
        try:
            hist_data = json.loads(requests.get('https://api-pub.bitfinex.com/v2/candles/trade:1m:{0}/hist?limit={1}'.format(self.symbol, limit)).text)
            hist_data.reverse()
            return np.array(hist_data)
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

    def get_sma_trading_condition(self):
        data = self.get_historical_data(1400)
        data = data[:, 2]
        data_sma = sma.simple_moving_average(data, 100)[100:]
        data = data[100:]
        trading_condition = self.get_sma_trading_condition_from_data(data, data_sma)
        return trading_condition

    def start_strategy_routine(self):
        while True:
            trading_condition = self.get_sma_trading_condition()
            self.dollar_amount = dollar_amount

            if not trading_condition == 'stable':
                if trading_condition == 'sma_above_below - buy':
                    is_successful, order_id = self.bitfinex_websocket_client.place_new_order(self.symbol, amount, price)
                    is_successful, order_id = self.bitfinex_websocket_client.place_new_order(self.symbol, amount, price)
                if trading_condition == 'sma_above_below - buy':
                    is_successful, order_id = self.bitfinex_websocket_client.place_new_order(self.symbol, amount, price)
                    is_successful, order_id = self.bitfinex_websocket_client.place_new_order(self.symbol, amount, price)


