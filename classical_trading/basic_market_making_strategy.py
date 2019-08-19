
import time as tm

import bitfinex as bt
import highest_spread_symbols as hss
import bitfinex_order_book_construction as bobc
import bitfinex_web_socket_auth as bwsa

ONE_PRECISION_POINT = 0.0001
SIDE_PRICE_DIFF_DICT = {'ask': -1, 'bid': 1}

def generic_find(l, lam):
    for i in range(len(l)):
        if lam(l[i]):
            return i

class BasicMarketMakingStrategy(object):
    def __init__(self, symbol, req_profit, amount):
        self.pricing_model = BasicMarketMakingPricingModel(ONE_PRECISION_POINT, amount)
        self.order_book = bobc.OrderBookThread(symbol)
        self.order_book.start()
        self.bitfinex_websocket_client = bwsa.get_authenticated_client()
        self.req_profit = req_profit
        self.symbol = symbol
        self.low_case_symbol = self.symbol[1:].lower()
        self.order_id_dictionary = {}
        self.amount = amount
        if not self.order_book.wsob.is_book_initialized:
            raise Exception('Order book did not initialized correctly.')

    def initiate_order(self, amount, side):
        current_price_dict = self.get_current_price_dict()
        alteration =  ONE_PRECISION_POINT * SIDE_PRICE_DIFF_DICT[side]
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
        return precedenes, current_book_dict[side][precedenes][1]

    def update_order(self, side, order_id, amount):
        precedenes, count = self.get_order_book_precedenes(side)
        if not (precedenes == 0 and count == 1):
            current_price_dict = self.get_current_price_dict()
            updated_price = current_price_dict[side] + ONE_PRECISION_POINT * SIDE_PRICE_DIFF_DICT[side]
            if not self.bitfinex_websocket_client.update_order(order_id, amount, updated_price):
                raise Exception('Unsuccessful order update.')

    def start_strategy_routine(self, amount):
        order_id_ask = self.initiate_order(amount, 'ask')
        order_id_bid = self.initiate_order(amount, 'bid')
        while True:
            precedenes_bid, count_bid = self.get_order_book_precedenes('bid')

class BasicMarketMakingPricingModel(object):
    def __init__(self, epsilon, trade_amount):
        self.epsilon = epsilon
        self.trade_amount = trade_amount

    def get_updated_order_prices(self, s_t, r_t, p_a_h, p_b_h, p_a_e, p_b_e, a_e_a, a_e_b, mu=0.001):
        a_l_a = self.trade_amount - a_e_a
        a_l_b = self.trade_amount - a_e_b
        #1
        if abs(p_a_h-p_b_h) >= s_t and a_e_a == 0 and a_e_b == 0:
            p_a = p_a_h - self.epsilon
            p_b = p_b_h + self.epsilon
            return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #2.A
        if abs(p_a_h-p_b_h) >= s_t and a_e_a > 0 and a_e_b == 0:
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
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_e * a_e_a + p_a_h * a_l_a)
            #3.A
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
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_e * a_e_a)
            if r_t <= p_a_e * a_e_a - p_b_e * a_e_b - p_b_h * a_l_b - f:
                p_b = p_b_h + self.epsilon
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_l_b}}
            else:
                p_b = (p_a_e * a_e_a - p_b_e * a_e_b - r_t - f)/a_l_b
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #5.B
        if a_l_b == 0 and a_e_a > 0:
            f = mu * ( p_b_e * a_e_b + p_a_e * a_e_a + p_a_h * a_l_a)
            if r_t <= p_a_e * a_e_a + p_a_h * a_l_a - p_b_e * a_e_b - f:
                p_a = p_a_h - self.epsilon
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':0, 'amount':0}}
            else:
                p_a = (p_b_e * a_e_b - p_a_e * a_e_a + r_t + f)/a_l_a
                return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':0, 'amount':0}}
        #6
        if abs(p_a_h-p_b_h) < s_t and a_e_a == 0 and a_e_b == 0:
            f = mu * (p_b_h * a_l_b + p_a_h * a_l_a)
            p_a = (p_a_h + p_b_h + (r_t + f) / a_l_a) / 2
            p_b = (p_a_h + p_b_h - (r_t + f) / a_l_a) / 2
            return {'ask':{'price':p_a, 'amount':a_l_a}, 'bid':{'price':p_b, 'amount':a_l_b}}
        #7
        if abs(p_a_h-p_b_h) < s_t:
            #7.A
            if a_e_a > 0 and a_e_b == 0:
                f = mu * (p_b_h * a_l_b + p_a_e * a_e_a + p_a_h * a_l_a)
                p_b = (p_a_e * a_e_a - r_t - f) / a_e_a
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_e_a}}
            #7.B
            if a_e_b > 0 and a_e_a == 0:
                f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_h * a_l_a)
                p_a = (p_b_e * a_e_b + r_t + f) / a_e_b
                return {'ask':{'price':p_a, 'amount':a_e_b}, 'bid':{'price':0, 'amount':0}}
        #8
        if abs(p_a_h-p_b_h) < s_t:
            f = mu * (p_b_e * a_e_b + p_b_h * a_l_b + p_a_e * a_e_a + p_a_h * a_l_a)
            #8.A
            if a_e_b > a_e_a:
                p_a = (r_t + p_b_e * a_e_b - p_a_e * a_e_a + f)/(a_e_b - a_e_a)
                return {'ask':{'price':p_a, 'amount':a_e_b - a_e_a}, 'bid':{'price':0, 'amount':0}}
            #8.B
            if a_e_a > a_e_b:
                p_b = (p_a_e * a_e_a - p_b_e * a_e_b - r_t - f)/(a_e_a - a_e_b)
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':p_b, 'amount':a_e_a - a_e_b}}
            #8.C 
            if a_e_a == a_e_b:
                return {'ask':{'price':0, 'amount':0}, 'bid':{'price':0, 'amount':0}}
