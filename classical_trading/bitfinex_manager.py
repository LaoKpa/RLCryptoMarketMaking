
import time as tm

import bitfinex_trade_wrapper as btw

class LimitOrderPosition:
    def __init__(self, bitfinex_trade_handler, order_info):
        self.bitfinex_trade_handler = bitfinex_trade_handler
        self.update_from_order_info(order_info)

    def update_from_order_info(self, order_info):
        self.price = float(order_info['price'])
        self.amount = float(order_info['original_amount'])
        self.is_active = bool(order_info['is_live'])
        self.order_id = int(order_info['order_id'])
        self.lower_case_symbol = order_info['symbol']
        self.side = order_info['side']

    def edit_limit_order_position(self, new_price, new_amount):
        if new_price == 0:
            new_price = self.price
        if new_amount == 0:
            new_amount = self.amount
        is_successful, order_info = self.bitfinex_trade_handler.replace_order(self.order_id, self.lower_case_symbol, new_amount, new_price, self.side, 'limit')
        if is_successful:
            self.update_from_order_info(order_info)
        else:
            raise Exception('Error replacing order.')

class BitfinexTradeManager:
    def __init__(self):
        self.bitfinex_trade_handler = btw.BitfinexTradeWrapper(btw.BITFINEX_KEY, btw.BITFINEX_SECRET)

    def put_order(self, amount, low_case_symbol, price, side):
        order_side = {'ask', 'sell', 'bid':'buy'}
        is_successful, result = self.bitfinex_trade_handler.place_order\
            (amount, price, order_side[side], 'limit', low_case_symbol)
        if is_successful:
            return LimitOrderPosition(self.bitfinex_trade_handler, result)
        else:
            raise Exception('Order failed.')

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
