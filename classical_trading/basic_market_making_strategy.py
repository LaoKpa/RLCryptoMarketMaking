
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

class BasicMarketMakingStrategy(object):
    def __init__(self, symbol, req_profit):
        self.order_book = bobc.OrderBookThread(symbol)
        self.order_book.start()
        self.req_profit = req_profit
        self.symbol = symbol
        self.low_case_symbol = self.symbol[1:].lower()
        if not self.order_book.wsob.is_book_initialized:
            raise Exception('Order book did not initialized correctly.')
        self.bid_position = LimitOrderPosition()
        self.ask_position = LimitOrderPosition()
    
    def get_position_by_side(self, side):
        return {'bid':self.bid_position, 'ask':self.ask_position}[side]

    def get_order_book_precedenes():
        current_ask_book = self.order_book.wsob.ask.copy()
        current_bid_bbok =  self.order_book.wsob.bid.copy()
        ask_precedenes = generic_find(current_ask_book, lambda item: item[0] == self.ask_position.price)
        bid_precedenes = generic_find(current_bid_book, lambda item: item[0] == self.bid_position.price)
        return ['ask_prec':ask_precedenes, 'bid_prec':bid_precedenes]

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
        print('test')

# self.price = 0
# self.amount = 0
# self.is_active = False
# self.is_filled = False
# self.is_initialized = False
# self.is_partially_filled = False
# self.filled_percentage = 0

    def profitability_treshold(self, price, side):
        if side == 'bid':
            bid_price = price
            ask_price = self.ask_position.price
        elif side == 'ask':
            bid_price = self.bid_position.price
            ask_price = price
        else:
            raise Exception('Undefined position side.')
        unit_profit = ask_price * (1 - 0.001) - bid_price * (1 + 0.001)
        unit_profit_percent = unit_profit / (ask_price + bid_price)
        if unit_profit_percent > self.req_profit:
            return [True, unit_profit_percent]
        else:
            return [False, unit_profit_percent]

    def basic_market_making_strategy(self):
        
    def rebalance_position(self, side):
        position = self.get_position_by_side(side)
        is_profitable, _ = self.profitability_treshold(new_price, side)
        if is_profitable:
            self.put_order(position.amount, new_peice)

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

