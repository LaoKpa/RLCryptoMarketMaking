
import imp
import time as tm
import pickle as pk
import threading
import numpy as np

from multiprocessing import Process, Manager, Lock
import multiprocessing as mp

CH = imp.load_source('config_helper', '../generic/config_helper.py')

ASKS_INDEX = 0
BIDS_INDEX = 1
ORDER_BOOK_KEYS = [ASKS_INDEX, BIDS_INDEX]

TIMESTAMP_INDEX = 0
PRICE_INDEX = 1
AMOUNT_INDEX = 2
MY_ORDER_INDEX = 3

DIRECTION_INDEX = 4
INDEX_INDEX = 5

TRADE_TYPE_INDEX = 3
TRADE_SELL_INDEX = 0
TRADE_BUY_INDEX = 1
TRADE_ID_INDEX = 4

class DataReader(object):
    def __init__(self, file_name):
        self.file_name = file_name

    def load_data(self, num_of_samples):
        with open(self.file_name, 'rb') as fh:
            self.data = np.load(fh).tolist()
        return self.data

class DataConveyer(object):
    def __init__(self, data):
        self.data = data
        self.sample_index = 0
        self.data_len = len(self.data)

    def get_next_sample(self):
        sample = self.data[self.sample_index]
        self.sample_index = (self.sample_index + 1) % self.data_len
        return sample.copy()

class StateSpace(object):
    def __init__(self, config):
        self.inventory = 0
        self.config = config
        self.available_funds = self.config.initial_investment
        self.initial_investment = self.config.initial_investment
        self.initial_price = 0

class OrderBook(object):
    def __init__(self, config_file_path, config_name, order_book_data_conveyer, trades):
        self.count = 0
        self.trade_count = 0
        self.transaction_history_buy = []
        self.transaction_history_sell = []
        self.order_book_data_conveyer = order_book_data_conveyer
        self.config = CH.ConfigHelper(config_file_path, config_name)
        self.order_book_transformer = OrderBookTransformator()
        self.current_order_book = self.order_book_data_conveyer.get_next_sample()
        self.next_order_book = self.order_book_data_conveyer.get_next_sample()
        self.trades = trades
        self.state_space = StateSpace(self.config)
        self.timestamp = self.current_order_book[ASKS_INDEX][0][TIMESTAMP_INDEX]
        self.sync_trade_clock()
        self.init_order_book()

    def init_order_book(self):
        self.order_book_transformer.transform_order_book(self.current_order_book)

    def get_net_worth(self):
        net_worth = self.state_space.available_funds + self.state_space.inventory * self.get_current_price()
        return net_worth

    def get_current_price(self):
        return (self.get_current_ask_price() + self.get_current_bid_price()) / 2.0

    def get_current_ask_price(self):
        for ask in self.current_order_book[ASKS_INDEX]:
            if not ask[MY_ORDER_INDEX]:
                current_ask_price = ask[PRICE_INDEX]
                return current_ask_price

    def get_current_bid_price(self):
        for bid in self.current_order_book[BIDS_INDEX]:
            if not bid[MY_ORDER_INDEX]:
                current_bid_price = bid[PRICE_INDEX]
                return current_bid_price

    def sync_trade_clock(self):
        while self.trades[self.trade_count][TIMESTAMP_INDEX] <= self.timestamp:
            self.trade_count += 1
    
    def get_total_amount_before_my_order(self, direction, order_book):
        count = 0
        total_amount = 0
        try:
            while not order_book[direction][count][MY_ORDER_INDEX]:
                total_amount += float(order_book[direction][count][AMOUNT_INDEX])
                count+=1
        except Exception as e:
            return (0, -1)
        return (total_amount, count)

    def unify_transactions(self, transaction_list):
        direction = transaction_list[0][TRADE_TYPE_INDEX]
        timestamp = transaction_list[0][TIMESTAMP_INDEX]
        amount = 0
        for transaction in transaction_list:
            amount += transaction[AMOUNT_INDEX]
            if not (direction == transaction[TRADE_TYPE_INDEX] and timestamp == transaction[TIMESTAMP_INDEX]):
                import pdb; pdb.set_trace()
        return {TIMESTAMP_INDEX:timestamp, AMOUNT_INDEX:amount, TRADE_TYPE_INDEX:direction}

    def settled_transaction_helper_helper(self, my_trade_count, transaction_list, my_transaction_list, total_before_my_order_amount):
        if my_trade_count >= 0 and len(transaction_list) > 0:
            unified_trade = self.unify_transactions(transaction_list)
            my_transaction_list.append(self.settled_transaction_helper(unified_trade, my_trade_count, total_before_my_order_amount))

    def settled_transaction_helper(self, unified_trade, my_trade_count, total_before_my_order_amount):
        transaction_amount = 0
        trade_direction = int(unified_trade[TRADE_TYPE_INDEX])
        transaction_price = self.current_order_book[trade_direction][my_trade_count][PRICE_INDEX]
        my_order_amount = self.current_order_book[trade_direction][my_trade_count][AMOUNT_INDEX]
        my_trade_amount = unified_trade[AMOUNT_INDEX] - total_before_my_order_amount
        if my_trade_amount > 0:
            if my_order_amount <= my_trade_amount:
                transaction_amount = my_order_amount
                self.order_book_transformer.delete_order(self.current_order_book[trade_direction][my_trade_count][INDEX_INDEX])
            else:
                transaction_amount = my_trade_amount
                self.order_book_transformer.change_order(self.current_order_book[trade_direction][my_trade_count][PRICE_INDEX],\
                    my_order_amount - my_trade_amount, self.current_order_book[trade_direction][my_trade_count][INDEX_INDEX])
        return {AMOUNT_INDEX:transaction_amount, PRICE_INDEX:transaction_price, TRADE_TYPE_INDEX:trade_direction}

    def settled_transaction(self):
        my_transaction_list = []
        transaction_list_ask = []
        transaction_list_bid = []
        tid_list = []
        if self.trades[self.trade_count][TIMESTAMP_INDEX] == self.timestamp:
            while len(self.trades) > self.trade_count and self.trades[self.trade_count][TIMESTAMP_INDEX] == self.timestamp:
                if not self.trades[self.trade_count][TRADE_ID_INDEX] in tid_list:
                    if self.trades[self.trade_count][TRADE_TYPE_INDEX] == ASKS_INDEX:
                        transaction_list_ask.append(self.trades[self.trade_count])
                    if self.trades[self.trade_count][TRADE_TYPE_INDEX] == BIDS_INDEX:
                        transaction_list_bid.append(self.trades[self.trade_count])
                    tid_list.append(self.trades[self.trade_count][TRADE_ID_INDEX])
                self.trade_count += 1
        total_before_my_order_amount_ask, my_trade_count_ask = self.get_total_amount_before_my_order(ASKS_INDEX, self.current_order_book)
        total_before_my_order_amount_bid, my_trade_count_bid = self.get_total_amount_before_my_order(BIDS_INDEX, self.current_order_book)
        self.settled_transaction_helper_helper(my_trade_count_ask, transaction_list_ask, my_transaction_list, total_before_my_order_amount_ask)
        self.settled_transaction_helper_helper(my_trade_count_bid, transaction_list_bid, my_transaction_list, total_before_my_order_amount_bid)
        return my_transaction_list

    def make_step(self):
        done = False
        if self.next_order_book[ASKS_INDEX][0][TIMESTAMP_INDEX] == self.timestamp:
            self.current_order_book = self.next_order_book
            self.next_order_book = self.order_book_data_conveyer.get_next_sample()
            self.count+=1
            self.order_book_transformer.transform_order_book(self.current_order_book)
        result_list = self.settled_transaction()
        self.update_state(result_list)
        if self.timestamp > self.trades[self.trade_count][TIMESTAMP_INDEX]:
            raise Exception()
        self.timestamp += 1
        if self.get_net_worth() <= 0:
            # import pdb; pdb.set_trace()
            done = True
        return done

    def update_state(self, list_of_transactions):
        for transaction in list_of_transactions:
            self.analyze_single_trnsaction(transaction)

    def analyze_single_trnsaction(self, settled_transaction):
        if settled_transaction[AMOUNT_INDEX] == 0:
            return 0
        if settled_transaction[TRADE_TYPE_INDEX] == TRADE_BUY_INDEX:
            self.state_space.inventory += settled_transaction[AMOUNT_INDEX]
            self.state_space.available_funds -= settled_transaction[AMOUNT_INDEX] * settled_transaction[PRICE_INDEX]
            self.transaction_history_buy.append((settled_transaction[AMOUNT_INDEX], settled_transaction[PRICE_INDEX]))
        elif settled_transaction[TRADE_TYPE_INDEX] == TRADE_SELL_INDEX:
            self.state_space.inventory -= settled_transaction[AMOUNT_INDEX]
            self.state_space.available_funds += settled_transaction[AMOUNT_INDEX] * settled_transaction[PRICE_INDEX]
            self.transaction_history_sell.append((settled_transaction[AMOUNT_INDEX], settled_transaction[PRICE_INDEX]))
        else:
            raise Exception('Unknown transaction type.')

class OrderBookTransformator(object):
    def __init__(self):
        self.alterations_list = []
        self.index = 0

    def insert_alteration(self, alteration, order_book):
        asks_book = order_book[ASKS_INDEX]
        bids_book = order_book[BIDS_INDEX]
        timestamp = order_book[ASKS_INDEX][0][TIMESTAMP_INDEX]
        if alteration[DIRECTION_INDEX] == TRADE_SELL_INDEX:
            alteration_price = alteration[PRICE_INDEX]
            ask_prices = [ask[PRICE_INDEX] for ask in asks_book]
            insertion_index = np.searchsorted(ask_prices, alteration_price)
            new_ask = {PRICE_INDEX: alteration_price, TIMESTAMP_INDEX:timestamp , AMOUNT_INDEX:alteration[AMOUNT_INDEX], MY_ORDER_INDEX:True, INDEX_INDEX:alteration[INDEX_INDEX]}
            order_book[ASKS_INDEX].insert(insertion_index, new_ask)
            order_book[ASKS_INDEX].pop()
        else:
            alteration_price = alteration[PRICE_INDEX]
            bid_prices = [bid[PRICE_INDEX] for bid in bids_book]
            bid_prices.reverse()
            insertion_index = len(bid_prices) - np.searchsorted(bid_prices, alteration_price, side='right')
            new_bid = {PRICE_INDEX: alteration_price, TIMESTAMP_INDEX:timestamp , AMOUNT_INDEX:alteration[AMOUNT_INDEX], MY_ORDER_INDEX:True, INDEX_INDEX:alteration[INDEX_INDEX]}
            order_book[BIDS_INDEX].insert(insertion_index, new_bid)
            order_book[BIDS_INDEX].pop()

    def transform_order_book(self, order_book):
        for alteration in self.alterations_list:
            self.insert_alteration(alteration, order_book)

    def add_order(self, price, amount, direction):
        self.index += 1
        self.alterations_list.append({PRICE_INDEX:price, AMOUNT_INDEX:amount, DIRECTION_INDEX:direction, INDEX_INDEX:self.index})
        return self.index    

    def change_order(self, price, amount, index):
        for alt in self.alterations_list:
            if alt[INDEX_INDEX] == index:
                self.alterations_list.remove(alt)
                alt[AMOUNT_INDEX] = amount
                alt[PRICE_INDEX] = price
                self.alterations_list.append(alt)
    
    def delete_order(self, index):
        for alt in self.alterations_list:
            if alt[INDEX_INDEX] == index:
                self.alterations_list.remove(alt)
    
    def delete_orders(self):
        self.alterations_list = []

class MarketMakingGame(object):
    def __init__(self, config_file_path, config_name, order_book_data_conveyer, trades):
        self.order_book = OrderBook(config_file_path, config_name, order_book_data_conveyer, trades)
        self.bots_ask_price = self.order_book.get_current_ask_price()
        self.bots_bid_price = self.order_book.get_current_bid_price()
        self.bots_ask_amount = self.order_book.get_net_worth() / self.order_book.get_current_price() * 0.1
        self.bots_bid_amount = self.order_book.get_net_worth() / self.order_book.get_current_price() * 0.1
        self.margin_coef = self.order_book.config.margin_coef
        self.order_index = None
        self.count = 0

    def get_data_conveyer(order_book_data_file_path, num_of_buffer_samples):
        dr = DataReader(order_book_data_file_path)
        dc = DataConveyer(dr.load_data(num_of_buffer_samples))
        return dc

    def make_action(self, ask_price, ask_amount, bid_price, bid_amount):
        self.bots_ask_price, self.bots_bid_price, self.bots_ask_amount, self.bots_bid_amount = ask_price, bid_price, ask_amount, bid_amount
        ask_order, bid_order = [(self.bots_ask_price, self.bots_ask_amount, TRADE_SELL_INDEX), (self.bots_bid_price, self.bots_bid_amount, TRADE_BUY_INDEX)]
        if self.order_index != None:
            self.count = 1
            if not self.order_index['ask'] == 0:
                self.order_book.order_book_transformer.delete_order(self.order_index['ask'])
            if not self.order_index['bid'] == 0:
                self.order_book.order_book_transformer.delete_order(self.order_index['bid'])
        else:
            if self.count > 0:
                import pdb; pdb.set_trace()
        portfolio_net_worth = self.order_book.get_net_worth()
        inventory = self.order_book.state_space.inventory
        price = self.order_book.get_current_price()
        ask_amount = ask_order[1]
        bid_amount = bid_order[1]
        ask_margin_condition = -1 * (inventory - ask_amount) * price / portfolio_net_worth < self.margin_coef
        bid_margin_condition = (inventory + bid_amount) * price / portfolio_net_worth < self.margin_coef
        if ask_margin_condition:
            ask_order_index = self.order_book.order_book_transformer.add_order(ask_order[0], ask_order[1], ask_order[2])
        else:
            ask_order_index = 0
        if bid_margin_condition:
            bid_order_index = self.order_book.order_book_transformer.add_order(bid_order[0], bid_order[1], bid_order[2])
        else:
            bid_order_index = 0
        self.order_index = {'ask':ask_order_index, 'bid':bid_order_index}
        step_done = self.order_book.make_step()

    def make_empty_action(self):
        self.order_book.make_step()
 