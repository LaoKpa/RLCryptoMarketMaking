
import imp
import time as tm
import pickle as pk
import threading
import numpy as np
import gym

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

    def get_next_sample(self):
        sample = self.data[self.sample_index]
        self.sample_index += 1
        return sample.copy()

class OneHot(object):
    def __init__(self, vector_size):
        self.one_hot_vector = np.zeros(vector_size)
        self.one_index = None
    
    def set_new_one(self, new_one_index):
        if self.one_index is not None:
            self.one_hot_vector[self.one_index] = 0
            self.one_hot_vector[new_one_index] = 1
        else:
            self.one_hot_vector[new_one_index] = 1
        self.one_index = new_one_index
        return self.one_hot_vector

    def get_one_hot(self):
        return self.one_hot_vector

class StateSpace(object):
    def __init__(self, config, order_book_state_generator):
        self.inventory = 0
        self.current_price = 0
        self.config = config
        self.available_funds = self.config.initial_investment
        self.initial_investment = self.config.initial_investment
        self.order_book_state_generator = order_book_state_generator
        self.order_book_state = None
        self.pos_funds_one_hot = OneHot(self.config.representation_vector_size)
        self.neg_funds_one_hot = OneHot(self.config.representation_vector_size)
        self.spread_one_hot = OneHot(self.config.representation_vector_size)
        self.ask_price_one_hot = OneHot(self.config.representation_vector_size)
        self.bid_price_one_hot = OneHot(self.config.representation_vector_size)
        self.pos_inventory_one_hot = OneHot(self.config.representation_vector_size)
        self.neg_inventory_one_hot = OneHot(self.config.representation_vector_size)
        self.bought_inventory_avg_price_one_hot = OneHot(self.config.representation_vector_size)
        self.position_in_ask_book_one_hot = OneHot(self.config.representation_vector_size)
        self.position_in_bid_book_one_hot = OneHot(self.config.representation_vector_size)
        self.price_diff_in_ask_book_one_hot = OneHot(self.config.representation_vector_size)
        self.price_diff_in_bid_book_one_hot = OneHot(self.config.representation_vector_size)
        self.wealth_accumulation_one_hot = OneHot(self.config.representation_vector_size)

    def get_pos_funds_representation(self):
        funds_ones_num = (self.available_funds / float(self.config.max_funds)) * self.config.funds_vector_size
        funds_ones_num = max(min(int(funds_ones_num), self.config.funds_vector_size - 1), 0)
        return self.funds_one_hot(funds_ones_num)

    def get_neg_funds_representation(self):
        funds_ones_num = (-self.available_funds / float(self.config.max_funds)) * self.config.funds_vector_size
        funds_ones_num = max(min(int(funds_ones_num), self.config.funds_vector_size - 1), 0)
        return self.funds_one_hot(funds_ones_num)

    def get_spread_representation(self, net_worth, price, ask_price, bid_price):
        spread_ones_num = 2 * (ask_price - bid_price)/(ask_price + bid_price) * 20 * 400
        return self.spread_one_hot(spread_ones_num)

    def get_price_representation(self, net_worth, price, ask_price, bid_price):
        return self.ask_price_one_hot

    def get_pos_inventory_representation(self, net_worth, price, ask_price, bid_price):
        margin_coeff = 3.0
        max_inventory = margin_coeff * (self.available_funds / float(self.current_price) + self.inventory)
        inventory_ones_num = (self.inventory / max_inventory) * self.config.inventory_vector_size        
        inventory_ones_num = max(min(int(inventory_ones_num), self.config.inventory_vector_size - 1), 0)
        return self.pos_inventory_one_hot(inventory_ones_num)

    def get_neg_inventory_representation(self, net_worth, price, ask_price, bid_price):
        margin_coeff = 3.0
        max_inventory = margin_coeff * (self.available_funds / float(self.current_price) + self.inventory)
        inventory_ones_num = (-self.inventory / max_inventory) * self.config.inventory_vector_size
        inventory_ones_num = max(min(int(inventory_ones_num), self.config.inventory_vector_size - 1), 0)
        return self.neg_inventory_one_hot((inventory_ones_num))

    def get_bought_inventory_avg_price_representation(self, net_worth, price, ask_price, bid_price):
        return self.bought_inventory_avg_price_one_hot

    def get_position_in_ask_book_representation(self, net_worth, price, ask_price, bid_price, my_order_position):
        my_ask_order_position, _, ask_book_length, _ = my_order_position
        position_in_ask_one_num = my_ask_order_position / ask_book_length * self.config.representation_vector_size
        return self.position_in_ask_book_one_hot(position_in_ask_one_num)

    def get_position_in_bid_book_representation(self, net_worth, price, ask_price, bid_price, my_order_position):
        _, my_bid_order_position, _, bid_book_length = my_order_position
        position_in_bid_one_num = my_bid_order_position / bid_book_length * self.config.representation_vector_size
        return self.position_in_bid_book_one_hot(position_in_bid_one_num)

    def get_price_diff_in_ask_book_representation(self, net_worth, price, ask_price, bid_price):
        return self.price_diff_in_ask_book_one_hot

    def get_price_diff_in_bid_book_representation(self, net_worth, price, ask_price, bid_price):
        return self.price_diff_in_bid_book_one_hot

    def get_wealth_accumulation_representation(self, net_worth, price, ask_price, bid_price):
        wealth_accumulation_one_num = (net_worth / self.initial_investment - 1) * self.config.representation_vector_size
        return self.wealth_accumulation_one_hot(wealth_accumulation_one_num)

    def get_state(self, net_worth, price, ask_price, bid_price):
        done = (self.available_funds <=0) and (self.inventory * self.current_price) <= 0 # change to minimum order limit
        return ((self.order_book_state[ASKS_INDEX], self.order_book_state[BIDS_INDEX],
            self.inventory_vector, self.funds_vector), done)

class OrderBookState(object):
    def __init__(self, order_book):
        self.cuurent_book = order_book
        self.previous_book = None
        
    def get_state_from_order_book(self, book, book_prev):
        ret = []
        for i in range(len(book)):
            bp = book[i][PRICE_INDEX]
            ba = book[i][AMOUNT_INDEX]
            bpp = book[i-1][PRICE_INDEX]
            p_tmp_1 = bp / book_prev[i][PRICE_INDEX]
            a_tmp_1 = ba / book_prev[i][AMOUNT_INDEX]
            if i == 0:
                p_tmp_2 = 1.0
                a_tmp_2 = 1.0
            else:
                p_tmp_2 = bp / bpp           
                a_tmp_2 = (bp * ba) / (bpp * book[i-1][AMOUNT_INDEX])
            ret.append([p_tmp_1-1.0, p_tmp_2-1.0, a_tmp_1-1.0, a_tmp_2-1.0, float(book[i][MY_ORDER_INDEX])])
        return np.array(ret)

    def get_order_book_state(self, book):
        self.cuurent_book = book
        self.previous_book = self.cuurent_book
        asks_state = self.get_state_from_order_book(self.cuurent_book[ASKS_INDEX], self.previous_book[ASKS_INDEX])
        bids_state = self.get_state_from_order_book(self.cuurent_book[BIDS_INDEX], self.previous_book[BIDS_INDEX])
        return {ASKS_INDEX:asks_state, BIDS_INDEX:bids_state}

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
        self.order_book_state = OrderBookState(self.current_order_book)
        self.state_space = StateSpace(self.config, self.order_book_state)
        self.timestamp = self.current_order_book[ASKS_INDEX][0][TIMESTAMP_INDEX]
        self.sync_trade_clock()
        self.init_order_book()

    def init_order_book(self):
        self.order_book_transformer.transform_order_book(self.current_order_book)

    def get_net_worth(self):
        net_worth = self.state_space.available_funds + self.state_space.inventory * self.get_current_price()
        return net_worth
    
    def get_my_order_position(self):
        my_ask_order_position = -1
        my_bid_order_position = -1
        for i in len(self.current_order_book[ASKS_INDEX]):
            if self.current_order_book[ASKS_INDEX][i][MY_ORDER_INDEX]:
                my_ask_order_position = i
        for i in len(self.current_order_book[BIDS_INDEX]):
            if self.current_order_book[BIDS_INDEX][i][MY_ORDER_INDEX]:
                my_bid_order_position = i
        return (my_ask_order_position, my_bid_order_position, len(self.current_order_book[ASKS_INDEX]), len(self.current_order_book[BIDS_INDEX]))

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
    
    def get_state(self):
        my_order_position = self.get_my_order_position()
        net_worth = self.get_net_worth()
        price = self.get_current_price()
        ask_price = self.get_current_ask_price()
        bid_price = self.get_current_bid_price()
        return self.state_space.get_state(net_worth, price, ask_price, bid_price, my_order_position)

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
        reward = 0
        if self.next_order_book[ASKS_INDEX][0][TIMESTAMP_INDEX] == self.timestamp:
            self.current_order_book = self.next_order_book
            self.next_order_book = self.order_book_data_conveyer.get_next_sample()
            self.count+=1
            self.order_book_transformer.transform_order_book(self.current_order_book)
        result_list = self.settled_transaction()
        self.update_state(result_list, self.current_order_book)
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
            self.transaction_history_buy.append(settled_transaction[AMOUNT_INDEX], settled_transaction[PRICE_INDEX])
        elif settled_transaction[TRADE_TYPE_INDEX] == TRADE_SELL_INDEX:
            self.state_space.inventory -= settled_transaction[AMOUNT_INDEX]
            self.state_space.available_funds += settled_transaction[AMOUNT_INDEX] * settled_transaction[PRICE_INDEX]
            self.transaction_history_sell.append(settled_transaction[AMOUNT_INDEX], settled_transaction[PRICE_INDEX])
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
            direction=ASKS_INDEX
            alteration_price = alteration[PRICE_INDEX]
            ask_prices = [ask[PRICE_INDEX] for ask in asks_book]
            insertion_index = np.searchsorted(ask_prices, alteration_price)
            new_ask = {PRICE_INDEX: alteration_price, TIMESTAMP_INDEX:timestamp , AMOUNT_INDEX:alteration[AMOUNT_INDEX], MY_ORDER_INDEX:True, INDEX_INDEX:alteration[INDEX_INDEX]}
            order_book[ASKS_INDEX].insert(insertion_index, new_ask)
            order_book[ASKS_INDEX].pop()
        else:
            direction=BIDS_INDEX
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

class ActionSpace(object):
    def __init__(self, config_file_path, config_name):
        self.config = CH.ConfigHelper(config_file_path, config_name)
    
    def calc_action_parameters(self, action):
        tmp_array = []
        v = action
        x = self.config.order_scale_size
        y = self.config.action_arg_num
        for i in range(y):
            b = v % x
            tmp_array.append(b)
            v = int((v-b)/int(x))
        return tmp_array

    def network_action_to_alteration(self, action, dim, current_ask_price, current_bid_price, available_funds, inventory):
        calc_price = lambda x: 1 + (x - 0.5) * 2 / float(50000)
        calc_amount = lambda x: (x + 1) * 0.1

        # action_vector = np.zeros(dim ** 4)
        # action_vector[action] = 1
        # action_tensor = action_vector.reshape([dim] * 4)
        # ask_price_arg, bid_price_arg, ask_amount_arg, bid_amount_arg = \
        #     (np.max(action_tensor.argmax(axis=i)) for i in range(4))

        ask_price_arg, bid_price_arg, ask_amount_arg, bid_amount_arg = self.calc_action_parameters(action)

        current_price = (current_ask_price + current_bid_price) / 2.0
        net_worth = available_funds + inventory * current_price
        suggested_ask_price = current_ask_price * calc_price(ask_price_arg / float(self.config.order_scale_size))
        suggested_bid_price = current_bid_price * calc_price(bid_price_arg / float(self.config.order_scale_size))
        
        # print('ask: {0}, ask_price: {1}, sugg_ask_price: {2}, bid: {3}, bid_price: {4}, sugg_bid_price: {5}'.format\
        #     (ask_price_arg, current_ask_price, suggested_ask_price, bid_price_arg, current_bid_price, suggested_bid_price))

        suggested_ask_amount = (net_worth / current_ask_price) * calc_amount(ask_amount_arg / float(self.config.order_scale_size))
        suggested_bid_amount = (net_worth / current_bid_price) * calc_amount(bid_amount_arg / float(self.config.order_scale_size))

        if suggested_ask_amount > 50 or suggested_bid_amount > 50:
            import pdb; pdb.set_trace()

        if suggested_ask_amount <= 0 or suggested_bid_amount <= 0:
            import pdb; pdb.set_trace()
        # print('{0} | ask: {1} | bid: {2} | {3}'.format(suggested_ask_amount, suggested_ask_price, suggested_bid_price, suggested_bid_amount))
        # print('real ask: {0} | real bid: {1}'.format(current_ask_price, current_bid_price))
        return [(suggested_ask_price, suggested_ask_amount, TRADE_SELL_INDEX), (suggested_bid_price, suggested_bid_amount, TRADE_BUY_INDEX)]

class Rewarder(object):
    def __init__(self):
        pass
    def get_reward(self, inv, prev_inv, funds, prev_funds, price):
        punishment = lambda x: 0.001 * ( (2 * x) ** 2  + x) + 0.001
        diff_inv = inv - prev_inv
        diff_funds = funds - prev_funds
        relative_inv = abs(inv) * price / funds
        if diff_inv == 0 and diff_funds == 0:
            p = -punishment(relative_inv)
            if p > 0:
                import pdb; pdb.set_trace()
            # print('PUNISHMENT: {0}'.format(p))
            return p
        current_net_worth = inv * price + funds
        prev_net_worth = prev_inv * price + prev_funds
        gain = current_net_worth - prev_net_worth
        # print('GAIN: {0}'.format(gain))
        return gain

class MarketMakingGame(object):
    def __init__(self, config_file_path, config_name, order_book_data_conveyer, trades):
        self.order_book = OrderBook(config_file_path, config_name, order_book_data_conveyer, trades)
        self.action_space = ActionSpace(config_file_path, config_name)
        self.rewarder = Rewarder()
        self.margin_coef = self.order_book.config.margin_coef
        self.order_index = None
        self.count = 0

    def get_state(self):
        return self.order_book.get_state()

    def make_action(self, action_vector):
        ask_order, bid_order = self.action_space.network_action_to_alteration(action_vector, 5,
        self.order_book.get_current_ask_price(), self.order_book.get_current_bid_price(),
        self.order_book.state_space.available_funds, self.order_book.state_space.inventory)
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
        tmp_inv = self.order_book.state_space.inventory
        tmp_funds = self.order_book.state_space.available_funds
        tmp_price = self.order_book.get_current_price()
        
        # print('nw1: {0}'.format(self.order_book.get_net_worth()))
        step_done = self.order_book.make_step()

        inv = self.order_book.state_space.inventory
        funds = self.order_book.state_space.available_funds
        price = self.order_book.get_current_price()
        # print('nw2: {0}'.format(self.order_book.get_net_worth()))

        reward = self.rewarder.get_reward(self.order_book.state_space.inventory, tmp_inv,
                                          self.order_book.state_space.available_funds, tmp_funds,
                                          self.order_book.get_current_price())

        state, done = self.order_book.get_state()
        if done:
            print('done')
            # import pdb; pdb.set_trace()
        if step_done:
            print('step done')
            # import pdb; pdb.set_trace()

        return {'state':state, 'reward':reward, 'done':(done or step_done)}

    def make_empty_action(self):
        self.order_book.make_step()
        state, done = self.order_book.get_state()
        return {'state':state, 'done':done}

    def get_total_reward(self):
        pass

    def is_episode_finished(self):
        pass

class GameWrapper(object):
    def __init__(self, game, nframes):
        self.game = game
        self.nframes = nframes
        self.current_state = [self.game.make_empty_action()['state'] for i in range(self.nframes)]

    def make_action(self, action):
        res = self.game.make_action(action)
        self.current_state.append(res['state'])
        self.current_state.pop(0)
        return (self.current_state, res['reward'], res['done'])

def parallel_game_environment_agent_map(args):
    env = args[0]
    action = args[1]
    num_of_frames = args[2]
    ask_book_batch, bid_book_batch, inv_batch, funds_batch = [], [], [], []
    state, reward, done = env.make_action(action)
    for i in range(num_of_frames):
        ask_book, bid_book, inv, funds = state[i]
        ask_book_batch.append(ask_book)
        bid_book_batch.append(bid_book)
        inv_batch.append(inv)
        funds_batch.append(funds)
    ############################################
    #         FIX ORDERING BY SORTING          #
    ############################################
    return ask_book_batch, bid_book_batch, inv_batch, funds_batch, reward, done

class ParallelGameEnvironment(object):
    def __init__(self, config_file_path, config_name):
        self.config = CH.ConfigHelper(config_file_path, config_name)
        t1 = tm.time()
        dcs = self.get_data_conveyer(self.config.order_book_base_path)
        print('Elapsed DCS: {0}.'.format(tm.time()-t1))
        with open(self.config.trades_file, 'rb') as fh:
            self.trades = np.load(fh)
        self.envs = [GameWrapper(MarketMakingGame(config_file_path, config_name, dcs[j], self.trades),
            self.config.num_of_frames) for j in range(self.config.num_of_envs)]
        self.initial_state = [env.current_state for env in self.envs]
        self.num_envs = self.config.num_of_envs
    
    def get_data_conveyer(self, order_book_base_path):
        dcs = []
        for i in range(self.config.num_of_envs):
            data_file_path = '{0}_{1}.bin'.format(order_book_base_path, i)
            dr = DataReader(data_file_path)
            dcs.append(DataConveyer(dr.load_data(self.config.num_of_buffer_samples)))
        return dcs

    def get_initial_state(self):
        ask_book_env_batch, bid_book_env_batch, inv_env_batch, funds_env_batch = [], [], [], []
        for env_state in self.initial_state:
            ask_book_batch, bid_book_batch, inv_batch, funds_batch = [], [], [], []
            for i in range(self.config.num_of_frames):
                ask_book, bid_book, inv, funds = env_state[i]
                ask_book_batch.append(ask_book)
                bid_book_batch.append(bid_book)
                inv_batch.append(inv)
                funds_batch.append(funds)
            ask_book_env_batch.append(ask_book_batch)
            bid_book_env_batch.append(bid_book_batch)
            inv_env_batch.append(inv_batch)
            funds_env_batch.append(funds_batch)
        return (np.array(ask_book_env_batch), np.array(bid_book_env_batch),
            np.array(inv_env_batch), np.array(funds_env_batch))

    def step(self, actions):
        t1 = tm.time()
        d = np.transpose(np.array(list(map(parallel_game_environment_agent_map, zip(self.envs, actions, [self.config.num_of_frames] * len(actions))))))
        t2 = tm.time()
        np_array = lambda r: [np.array(r[i]) for i in range(len(r))]
        ask_book_env_batch = np.array(np_array(d[0]))
        bid_book_env_batch = np.array(np_array(d[1]))
        inv_env_batch = np.array(np_array(d[2]))
        funds_env_batch = np.array(np_array(d[3]))
        rewards_env_batch = np.array(np_array(d[4]))
        dones_env_batch = np.array(np_array(d[5]))
        return (((ask_book_env_batch), (bid_book_env_batch),
            (inv_env_batch), (funds_env_batch)), (rewards_env_batch), (dones_env_batch), t2-t1)
