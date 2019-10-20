
import imp
import time as tm
import pickle as pk
import numpy as np

import market_making_game as mmg

CH = imp.load_source('config_helper', '../generic/config_helper.py')

ORDER_BOOK_SAMPLE = {
    'bids':
        [{'timestamp': 1550567912.0, 'amount': 1.0625039, 'price': 3999.7},
        {'timestamp': 1550567912.0, 'amount': 0.2, 'price': 3999.5},
        {'timestamp': 1550567912.0, 'amount': 1.97994482, 'price': 3999.3},
        {'timestamp': 1550567912.0, 'amount': 0.69085051, 'price': 3999.1},
        {'timestamp': 1550567912.0, 'amount': 0.02, 'price': 3999.0}],
    'asks':
        [{'timestamp': 1550567912.0, 'amount': 30.36140167, 'price': 3999.8},
        {'timestamp': 1550567912.0, 'amount': 0.39816565, 'price': 3999.9},         
        {'timestamp': 1550567912.0, 'amount': 49.74176247, 'price': 4000.0},        
        {'timestamp': 1550567912.0, 'amount': 0.16812499, 'price': 4000.6},         
        {'timestamp': 1550567912.0, 'amount': 8.0, 'price': 4000.8}]
                    }

TRADE = {
            'amount': '0.05',
            'exchange': 'bitfinex',
            'timestamp': 1550567912,
            'price': '3999.8',
            'tid': 338912171,
            'type': 'buy'
        }

LIMIT_ORDERS = [(3999.77, 0.1, 'sell'), (3999.72, 0.1, 'buy')]


# def transform_order_book(self, order_book):
# index = def add_order(self, price, amount, direction):
# def change_order(self, price, amount, index):
# def delete_order(self, index):
# def delete_orders(self):

class OrderBookTester(object):
    def __init__(self, config_file_path, config_name):
        self.order_book = mmg.OrderBook(config_file_path, config_name)
        self.order_book_transformer = mmg.OrderBookTransformator()
    
    def test_settlement_mechanism(self):
        for order in LIMIT_ORDERS:
            self.order_book_transformer.add_order(*order)
        self.order_book_transformer.transform_order_book(ORDER_BOOK_SAMPLE)
        print(self.order_book.settle_trade(TRADE, ORDER_BOOK_SAMPLE))

def main_order_book_tester():
    obt = OrderBookTester('../configs/btc_market_making_config.txt', 'MARKET_MAKING_CONFIG')
    obt.test_settlement_mechanism()

def main():
    main_order_book_tester()
    order_price_scale_size = 5
    current_ask_price = 3997.5
    calc_price = lambda x: 1 + (x - 0.5) * 2 / float(100000)
    choices = [current_ask_price * calc_price(ask_price_arg / float(order_price_scale_size))\
                for ask_price_arg in range(order_price_scale_size)]
    print(choices)

if __name__ == "__main__":
    main()
