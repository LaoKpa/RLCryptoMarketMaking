
import time as tm

import bitfinex as bt
import highest_spread_symbols as hss
import bitfinex_trade_wrapper as btw
import bitfinex_order_book_construction as bobc

ONE_PRECISION_POINT = 0.0001

def generic_find(l, lam):
    for i in range(len(l)):
        if lam(l[i]):
            return i

class LimitOrderPosition:
    def __init__(self):
        self.price = 0
        self.amount = 0
        self.is_active = False
        self.is_filled = False
        self.is_initialized = False
        self.is_partially_filled = False
        self.filled_percentage = 0

class BasicMarketMakingStrategy(object):
    def __init__(self, symbol):
        self.order_book = bobc.OrderBookThread(symbol)
        self.order_book.start()
        self.symbol = symbol
        self.low_case_symbol = self.symbol[1:].lower()
        if not self.order_book.wsob.is_book_initialized:
            raise Exception('Order book did not initialized correctly.')
        self.bitfinex_trade_handler = btw.BitfinexTradeWrapper(btw.BITFINEX_KEY, btw.BITFINEX_SECRET)
        self.bid_position = LimitOrderPosition()
        self.ask_position = LimitOrderPosition()

    def get_order_book_precedenes():
        current_ask_book = self.order_book.wsob.ask.copy()
        current_bid_bbok =  self.order_book.wsob.bid.copy()
        generic_find(current_ask_book, lambda item: item[0])

    def put_bid_order(self, amount, price):
        return self.bitfinex_trade_handler.place_order\
            (amount, price, 'buy', 'limit', self.low_case_symbol)

    def put_ask_order(self, amount, price):
        return self.bitfinex_trade_handler.place_order\
            (amount, price, 'sell', 'limit', self.low_case_symbol)

    def check_for_other_bots(self):
        current_ask_price = self.order_book.wsob.get_ask_price()
        current_bid_price = self.order_book.wsob.get_bid_price()


    def set_bid_ask_orders_current_price(self):
        current_ask_price = self.order_book.wsob.get_ask_price()
        current_bid_price = self.order_book.wsob.get_bid_price()
        t1 = tm.time()
        res = self.put_bid_order(10.0, current_bid_price)
        t2 = tm.time()
        print('Order Elapsed: {0}.', t2-t1)
        import pudb; pudb.set_trace()
        print('duck')

"""
Get bid/ask prices
Set positions to current bid/ask
Check if there are bots fighting with you:
    Increase bid/ask by one precision point:
        If someone instantely gets a head -> there is competition
        If not -> there is no competition
If there is competition:
    Try to get first in line:
        Increase/Descrease bid/ask while keeping a profitable margin until first in line
"""

# 
# {'exchange': 'bitfinex',
#  'is_cancelled': False,
#  'gid': None,
#  'timestamp': '1560266870.53677338',
#  'price': '1.6459',
#  'side': 'buy',
#  'original_amount': '10.0',
#  'avg_execution_price': '0.0',
#  'symbol': 'etpusd',
#  'id': 26557157187,
#  'is_live': True,
#  'cid_date': '2019-06-11',
#  'order_id': 26557157187,
#  'was_forced': False,
#  'oco_order': None,
#  'remaining_amount': '10.0',
#  'executed_amount': '0.0',
#  'cid': 55670522797,
#  'type': 'limit',
#  'src': 'api',
#  'is_hidden': False}
