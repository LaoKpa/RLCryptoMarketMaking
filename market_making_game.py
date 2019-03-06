
import pickle as pk
import numpy as np

import config_helper as ch



class OrderBook(object):
    def __init__(self, config_file_path, config_name):
        self.config = ch.ConfigHelper(config_file_path, config_name)
        self.order_book_file_handler = open(self.config.order_book_file, 'rb')
        self.trades_file_handler = open(self.config.trades_file, 'rb')
        self.current_order_book = pk.load(self.order_book_file_handler)
        self.trades = pk.load(self.trades_file_handler)
        self.timestamp = self.current_order_book['asks'][0]['timestamp']
        self.count = 0

    def advance_clock(self):
        self.timestamp += 1
        self.count += 1

    def make_step(self):
        pass

class OrderBookTransformator(object):
    def __init__(self):
        self.alterations_list = []

    def insert_alteration(self, alteration, order_book):
        asks_book = order_book['asks']
        bids_book = order_book['bids']
        timestamp = order_book['asks'][0]['timestamp']
        if alteration[2]:
            direction='asks'
            alteration_price = alteration[0]
            ask_prices = [ask['price'] for ask in asks_book]
            insertion_index = np.searchsorted(ask_prices, alteration_price)
            new_ask = {'price': alteration_price, 'timestamp':timestamp , 'amount':alteration[1], 'my_order':True}
            order_book['asks'].insert(insertion_index, new_ask)
            order_book['asks'].pop()
        else:
            direction='bids'
            alteration_price = alteration[0]
            bid_prices = [bid['price'] for bid in bids_book]
            bid_prices.reverse()
            insertion_index = len(bid_prices) - np.searchsorted(bid_prices, alteration_price, side='right')
            new_bid = {'price': alteration_price, 'timestamp':timestamp , 'amount':alteration[1], 'my_order':True}
            order_book['bids'].insert(insertion_index, new_bid)
            order_book['bids'].pop()

    def add_my_order_indicator(self, order_book):
        for order_type in order_book.keys():
            for i in range(len(order_book[order_type])):
                order_book[order_type][i]['my_order'] = False

    def transform_order_book(self, order_book):
        self.add_my_order_indicator(order_book)
        for alteration in self.alterations_list:
            self.insert_alteration(alteration, order_book)

    def add_order(self, price, amount, direction):
        self.alterations_list.append((price, amount, direction))

    def delete_orders(self):
        self.alterations_list = []

class MarketMakingGame(object):
    def __init__(self, config_file_path, config_name):
        self.config = ch.ConfigHelper(config_file_path, config_name)
        self.order_book_file_handler = open(self.config.order_book_file, 'rb')
        self.timestamp = 0

    def get_state_from_order_book(self, book, book_prev):
        ret = []
        for i in range(len(book)):
            p_tmp_1 = book[i]['price'] / book_prev[i]['price']
            if i == 0:
                p_tmp_2 = 1.0
            else:
                p_tmp_2 = book[i]['price'] / book[i-1]['price']           
            a_tmp_1 = book[i]['amount'] / book_prev[i]['amount']
            if i == 0:
                a_tmp_2 = 1.0
            else:
                a_tmp_2 = (book[i]['price'] * book[i]['amount']) / (book[i-1]['price'] * book[i-1]['amount'])
            ret.append([p_tmp_1-1.0, p_tmp_2-1.0, a_tmp_1-1.0, a_tmp_2-1.0])
        return np.array(ret)
    
    def get_state(self):
        if self.timestamp == 0:
            order_book_prev = pk.load(self.order_book_file_handler)
            order_book = pk.load(self.order_book_file_handler)
            self.timestamp = order_book_prev['asks'][0]['timestamp']
            return (self.get_state_from_order_book(order_book['asks'], order_book_prev['asks']),
                    self.get_state_from_order_book(order_book['bids'], order_book_prev['bids']))
        else:
            pass
            
    def make_action(self, action):
        pass

    def get_total_reward(self):
        pass

    def is_episode_finished(self):
        pass

    def get_total_reward(self):
        pass

# game.init()
# game.new_episode()
# state = game.get_state()
# reward = game.make_action(action)
# game.get_total_reward()
# done = game.is_episode_finished()
# score = game.get_total_reward()
# game.get_available_buttons_size()
# game.close()
