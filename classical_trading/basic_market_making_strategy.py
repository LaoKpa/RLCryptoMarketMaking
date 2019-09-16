
import time as tm

import logging
import tabulate as tb

import bitfinex as bt
import highest_spread_symbols as hss
import bitfinex_order_book_construction as bobc
import bitfinex_web_socket_auth as bwsa

ONE_PRECISION_POINT = 0.0001
SIDE_PRICE_DIFF_DICT = {'ask': -1, 'bid': 1}

logging.basicConfig(filename='basic_market_making.log',level=logging.DEBUG)

def generic_find(l, lam):
    for i in range(len(l)):
        if lam(l[i]):
            return i
    return -1

class BasicMarketMakingStrategy(object):
    def __init__(self, symbol, req_spread_percntage, dollar_amount):
        self.order_book = bobc.OrderBookThread(symbol)
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

    def get_order_book_precedenes(self, side):
        current_book_dict = self.get_current_book_dict()
        if side in self.order_id_dictionary:
            order_representation = self.bitfinex_websocket_client.get_order_representation(self.order_id_dictionary[side])
        else:
            raise Exception('No order matches order side.')
        precedenes = generic_find(current_book_dict[side], lambda item: item[0] == order_representation.price)
        if precedenes >= 0:
            return precedenes, current_book_dict[side][precedenes][1]
        else:
            return precedenes, 0

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

    def release_resources(self):
        self.order_book.close_thread()
        self.bitfinex_websocket_client.close_thread()

    def start_strategy_routine(self):
        price_dict = self.get_current_price_dict()
        price = (price_dict['ask'] + price_dict['bid']) / 2
        amount = self.dollar_amount / price
        order_id_ask = self.initiate_order(amount, 'ask')
        order_id_bid = self.initiate_order(amount, 'bid')
        s_t = self.req_spread_percntage * price
        r_t = s_t * amount
        self.pricing_model = BasicMarketMakingPricingModel(ONE_PRECISION_POINT, amount)
        while True:
            tm.sleep(0.1)
            logging.debug('Start of market making loop.')
            p_a_h = self.get_current_price('ask')
            p_b_h = self.get_current_price('bid')
            p_a_e = self.bitfinex_websocket_client.active_orders[order_id_ask].exec_price
            p_b_e = self.bitfinex_websocket_client.active_orders[order_id_bid].exec_price
            a_e_a = self.bitfinex_websocket_client.active_orders[order_id_ask].exec_amount
            a_e_b = self.bitfinex_websocket_client.active_orders[order_id_bid].exec_amount
            print(tb.tabulate([['p_a_h', p_a_h],['p_b_h', p_b_h],['p_a_e', p_a_e],['p_b_e', p_b_e],['a_e_a', a_e_a],['a_e_b', a_e_b]]))
            order_update_dict = self.pricing_model.get_updated_order_prices(s_t, r_t, p_a_h, p_b_h, p_a_e, p_b_e, abs(a_e_a), abs(a_e_b))
            print(order_update_dict)
            ask_order_finished = self.bitfinex_websocket_client.active_orders[order_id_ask].amount == 0
            bid_order_finished = self.bitfinex_websocket_client.active_orders[order_id_bid].amount == 0
            logging.debug('Ask amount left: {0}'.format(self.bitfinex_websocket_client.active_orders[order_id_ask].amount))
            logging.debug('Bid amount left: {0}'.format(self.bitfinex_websocket_client.active_orders[order_id_bid].amount))
            if not ask_order_finished:
                logging.debug('Update order ask.')
                self.update_order(order_id_ask, order_update_dict['ask']['amount'], order_update_dict['ask']['price'], 'ask')
            if not bid_order_finished:
                logging.debug('Update order bid.')
                self.update_order(order_id_bid, order_update_dict['bid']['amount'], order_update_dict['bid']['price'], 'bid')
            if ask_order_finished and bid_order_finished:
                logging.debug('Finish.')
                self.release_resources()
                return True

class BasicMarketMakingPricingModel(object):
    def __init__(self, epsilon, trade_amount):
        self.epsilon = epsilon
        self.trade_amount = trade_amount

    def get_updated_order_prices(self, s_t, r_t, p_a_h, p_b_h, p_a_e, p_b_e, a_e_a, a_e_b, mu=0.001):
        a_l_a = self.trade_amount - a_e_a
        a_l_b = self.trade_amount - a_e_b
        #1
        if abs(p_a_h - p_b_h) >= s_t and a_e_a == 0 and a_e_b == 0:
            print('Pricing Model: #1')
            p_a = p_a_h - self.epsilon
            p_b = p_b_h + self.epsilon
            return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #2.A
        if abs(p_a_h-p_b_h) >= s_t and a_e_a > 0 and a_e_b == 0:
            print('Pricing Model: #2.A')
            f = mu * (p_a_e * a_e_a + p_a_h * a_l_a + p_b_h * a_l_b)
            if r_t - p_a_e * a_e_a <= p_a_h * a_l_a - p_b_h * a_l_b - f:
                p_a = p_a_h - self.epsilon
                p_b = p_b_h + self.epsilon
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
            else:
                p_a = p_a_h - self.epsilon
                p_b = (p_a_e * a_e_a + p_a_h * a_l_a - r_t - f) / a_l_b
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #2.B
        if abs(p_a_h-p_b_h) >= s_t and a_e_b > 0 and a_e_a == 0:
            print('Pricing Model: #2.B')
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_h * a_l_a)
            if r_t + p_b_e * a_e_b <= p_a_h * a_l_a - p_b_h * a_l_b - f:
                p_a = p_a_h - self.epsilon
                p_b = p_b_h + self.epsilon
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
            else:
                p_a = (p_b_e * a_e_b + p_b_h * a_l_b + r_t + f) / a_l_a
                p_b = p_b_h + self.epsilon
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #3
        if abs(p_a_h-p_b_h) >= s_t and a_e_b > 0 and a_e_a > 0:
            print('Pricing Model: #3')
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_e * a_e_a + p_a_h * a_l_a)
            #3.A
            print('Pricing Model: #3.A')
            if a_e_b >  a_e_a:
                if r_t + p_b_e * a_e_b - p_a_e * a_e_a <= p_a_h * a_l_a - p_b_h * a_l_b - f:
                    p_a = p_a_h - self.epsilon
                    p_b = p_b_h + self.epsilon
                    return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
                else:
                    p_a = p_b_h - self.epsilon
                    p_b = (p_a_e * a_e_a - p_b_e * a_e_b + p_a_h * a_l_a - r_t - f) / a_l_b
                    return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
            #3.B
            if a_e_a >  a_e_b:
                print('Pricing Model: #3.B')
                if r_t + p_b_e * a_e_b - p_a_e * a_e_a <= p_a_h * a_l_a - p_b_h * a_l_b - f:
                    p_a = p_a_h - self.epsilon
                    p_b = p_b_h + self.epsilon
                    return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
                else:
                    p_a = ( p_b_e * a_e_b - p_a_e * a_e_a + p_b_h * a_l_b + r_t + f) / a_l_a
                    p_b = p_b_h + self.epsilon
                    return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #4.A
        if a_l_a == 0 and a_e_b == 0:
            print('Pricing Model: #4.A')
            f = mu * (p_b_h * a_l_b + p_a_e * a_e_a)
            if r_t <= p_a_e * a_e_a - p_b_h * a_l_b - f:
                p_a = 0
                p_b = p_b_h + self.epsilon
                return {'ask':{'price':p_a, 'amount':0}, 'bid':{'price':p_b, 'amount':a_l_b}}
            else:
                p_a = 0
                p_b = (p_a_e * a_e_a - r_t - f)/a_l_b
                return {'ask':{'price':p_a, 'amount':0}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #4.B
        if a_l_b == 0 and a_e_a == 0:
            print('Pricing Model: #4.B')
            f = mu * (p_b_e * a_e_b + p_a_h * a_l_a)
            if r_t <= p_a_h * a_l_a - p_b_e * a_e_b - f:
                p_b = 0
                p_a = p_a_h - self.epsilon
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':0}}
            else:
                p_b = 0
                p_a = (p_b_e * a_e_b + r_t + f)/a_l_a
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':0}}
        #5.A
        if a_l_a == 0 and a_e_b > 0:
            print('Pricing Model: #5.A')
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_e * a_e_a)
            if r_t <= p_a_e * a_e_a - p_b_e * a_e_b - p_b_h * a_l_b - f:
                p_b = p_b_h + self.epsilon
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_l_b}}
            else:
                p_b = (p_a_e * a_e_a - p_b_e * a_e_b - r_t - f)/a_l_b
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #5.B
        if a_l_b == 0 and a_e_a > 0:
            print('Pricing Model: #5.B')
            f = mu * ( p_b_e * a_e_b + p_a_e * a_e_a + p_a_h * a_l_a)
            if r_t <= p_a_e * a_e_a + p_a_h * a_l_a - p_b_e * a_e_b - f:
                p_a = p_a_h - self.epsilon
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':0, 'amount':0}}
            else:
                p_a = (p_b_e * a_e_b - p_a_e * a_e_a + r_t + f)/a_l_a
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':0, 'amount':0}}
        #6
        if abs(p_a_h-p_b_h) < s_t and a_e_a == 0 and a_e_b == 0:
            print('Pricing Model: #6')
            f = mu * (p_b_h * a_l_b + p_a_h * a_l_a)
            p_a = (p_a_h + p_b_h + (r_t + f) / a_l_a) / 2
            p_b = (p_a_h + p_b_h - (r_t + f) / a_l_a) / 2
            return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #7
        if abs(p_a_h-p_b_h) < s_t:
            print('Pricing Model: #7')
            #7.A
            if a_e_a > 0 and a_e_b == 0:
                print('Pricing Model: #7.A')
                f = mu * (p_b_h * a_l_b + p_a_e * a_e_a + p_a_h * a_l_a)
                p_b = (p_a_e * a_e_a - r_t - f) / a_e_a
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_e_a}}
            #7.B
            if a_e_b > 0 and a_e_a == 0:
                print('Pricing Model: #7.B')
                f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_h * a_l_a)
                p_a = (p_b_e * a_e_b + r_t + f) / a_e_b
                return {'ask':{'price':p_a, 'amount':a_e_b}, 'bid':{'price':0, 'amount':0}}
        #8
        if abs(p_a_h-p_b_h) < s_t:
            print('Pricing Model: #8')
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_e * a_e_a + p_a_h * a_l_a)
            #8.A
            if a_e_b > a_e_a:
                print('Pricing Model: #8.A')
                p_a = (r_t + p_b_e * a_e_b - p_a_e * a_e_a + f)/(a_e_b - a_e_a)
                return {'ask':{'price':p_a, 'amount':a_e_b - a_e_a}, 'bid':{'price':0, 'amount':0}}
            #8.B
            if a_e_a > a_e_b:
                print('Pricing Model: #8.B')
                p_b = (p_a_e * a_e_a - p_b_e * a_e_b - r_t - f)/(a_e_a - a_e_b)
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_e_a - a_e_b}}
            #8.C
            if a_e_a == a_e_b:
                print('Pricing Model: #8.C')
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':0, 'amount':0}}
        import pdb; pdb.set_trace()
        print('placeholder')
