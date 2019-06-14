
import time as tm

import bitfinex as bt
import highest_spread_symbols as hss
import bitfinex_trade_wrapper as btw
import bitfinex_order_book_construction as bobc

class BasicMarketMakingStrategy:
    def __init__(self, symbol):
        self.order_book = bobc.OrderBookThread(symbol)
        self.order_book.start()
        self.symbol = symbol
        self.low_case_symbol = self.symbol[1:].lower()
        if not self.order_book.wsob.is_book_initialized:
            raise Exception('Order book did not initialized correctly.')
        self.bitfinex_trade_handler = btw.BitfinexTradeWrapper(btw.BITFINEX_KEY, btw.BITFINEX_SECRET)

    def set_bid_ask_orders_current_price(self):
        current_ask_price = self.order_book.wsob.get_ask_price()
        current_bid_price = self.order_book.wsob.get_bid_price()
        t1 = tm.time()
        res = self.bitfinex_trade_handler.place_order\
            (10.0, current_bid_price, 'buy', 'limit', self.low_case_symbol)
        t2 = tm.time()
        print('Order Elapsed: {0}.', t2-t1)
        import pudb; pudb.set_trace()
        print('duck')

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
