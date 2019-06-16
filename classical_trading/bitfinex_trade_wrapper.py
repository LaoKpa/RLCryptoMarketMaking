
import time as tm

import bitfinex_trade_client as btc

from termcolor import cprint

BITFINEX_KEY = "N1bQYgTEzuDvzwYcpFXhiv1So0Df1IhoVj8wWQvczqT"
BITFINEX_SECRET = "L5LUl8e65GRsxMd28naxTL5dITticeD6mKTSloUDcG3"

class BitfinexTradeWrapper(object):
    def __init__(self, bitfinex_key, bitfinex_secret):
        self.bitfinex_object = btc.TradeClient(bitfinex_key, bitfinex_secret)
        self.is_position_open = False
        self.buy_history = list()
        self.sell_history = list()
        self.position_price = 0
        self.position_volume = 0
        self.trade_pair = str()

    def get_margin_info(self):
        query_result = None
        while True:
            try:
                query_result = self.bitfinex_object.margin_infos()
                result = query_result[0]['tradable_balance']
                break
            except Exception as e:
                cprint('API crashed while querying margin info.', 'blue')
                cprint(e, 'red')
        return result

    def replace_order(self, order_id, symbol, amount, price, side, ordertype):
        try:
            result = self.bitfinex_object.replace_order(order_id, symbol, str(amount), str(price), side, ordertype)
        except Exception as e:
            cprint('Exception Occured In {0} order: {1}. Type: {2}.'.\
            format(order, e, type(e)), 'blue')
            import pdb; pdb.set_trace()
            return [False, None]
        return [True, result]

    def place_order(self, amount, price, side, ordertype, symbol):
        try:
            result = self.bitfinex_object.place_order(str(amount), str(price), side, ordertype, symbol)
        except Exception as e:
            cprint('Exception Occured In {0} order: {1}. Type: {2}.'.\
            format(order, e, type(e)), 'blue')
            import pdb; pdb.set_trace()
            return [False, None]
        return [True, result]

    def get_order_id(self, order_result, err_msg):
        try:
            order_id = order_result['id']
        except Exception as e:
            cprint(order_result, 'blue')
            cprint('Exception Occured In {1} Order Information: {0}.'.format(e, err_msg), 'blue')
            return False
        return order_id

    def get_order_info(self, order_id, position, err_msg):
        query_result = None
        while True:
            try:
                query_result = self.bitfinex_object.status_order(order_id)
                if not query_result['is_live'] and not query_result['is_cancelled']:
                    self.is_position_open = position
                    break
                if not query_result['is_live'] and query_result['is_cancelled']:
                    import pdb; pdb.set_trace()
                time.sleep(10)
            except Exception as e:
                print (query_result, order_id, position, err_msg)
                cprint('API Crash while querying {0} orders: {1} .'.\
                format(err_msg, e), 'blue')
        return query_result
