
import pdb
import pickle as pk
import numpy as np
import config_helper as ch

class StateSpace(object):
    def __init__(self, config, order_book_state_generator):
        self.config = config
        self.inventory = 0
        self.current_price = 0
        self.available_funds = self.config.initial_investment
        self.order_book_state_generator = order_book_state_generator
        self.order_book_state = None

    def update_state(self, list_of_transactions, book):
        for transaction in list_of_transactions:
            self.analyze_single_trnsaction(transaction)
        self.order_book_state = self.order_book_state_generator.get_order_book_state(book)

    def analyze_single_trnsaction(self, settled_transaction):
        print(settled_transaction)
        if settled_transaction['amount'] == 0:
            return 0
        if settled_transaction['type'] == 'buy':
            self.inventory += settled_transaction['amount']
            self.available_funds -= settled_transaction['amount'] * settled_transaction['price']
            self.current_price = settled_transaction['price']
        elif settled_transaction['type'] == 'sell':
            self.inventory -= settled_transaction['amount']
            self.available_funds += settled_transaction['amount'] * settled_transaction['price']
            self.current_price = settled_transaction['price']
        else:
            raise Exception('Unknown transaction type.')

    def get_state(self):
        max_inventory = self.available_funds / float(self.current_price) + self.inventory
        inventory_ones_num = (self.inventory / max_inventory) * self.config.inventory_vector_size
        inventory_vector = np.array([float(i < inventory_ones_num) for i in range(self.config.inventory_vector_size)])
        funds_ones_num = (self.available_funds / float(self.config.max_funds)) * self.config.funds_vector_size
        funds_vector = np.array([float(i < funds_ones_num) for i in range(self.config.funds_vector_size)])
        return (self.order_book_state['asks'], self.order_book_state['bids'], inventory_vector, funds_vector)

class OrderBookState(object):
    def __init__(self, order_book):
        self.cuurent_book = order_book
        self.previous_book = None
        
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
            ret.append([p_tmp_1-1.0, p_tmp_2-1.0, a_tmp_1-1.0, a_tmp_2-1.0, float(book[i]['my_order'])])
        return np.array(ret)

    def get_order_book_state(self, book):
        self.cuurent_book = book
        self.previous_book = self.cuurent_book
        asks_state = self.get_state_from_order_book(self.cuurent_book['asks'], self.previous_book['asks'])
        bids_state = self.get_state_from_order_book(self.cuurent_book['bids'], self.previous_book['bids'])
        return {'asks':asks_state, 'bids':bids_state}

class OrderBook(object):
    def __init__(self, config_file_path, config_name):
        self.trade_count = 0
        self.config = ch.ConfigHelper(config_file_path, config_name)
        self.order_book_transformer = OrderBookTransformator()
        self.order_book_file_handler = open(self.config.order_book_file, 'rb')
        self.trades_file_handler = open(self.config.trades_file, 'rb')
        self.current_order_book = pk.load(self.order_book_file_handler)
        self.next_order_book = pk.load(self.order_book_file_handler)
        self.trades = pk.load(self.trades_file_handler)
        self.order_book_state = OrderBookState(self.current_order_book)
        self.state_space = StateSpace(self.config, self.order_book_state)
        self.timestamp = self.current_order_book['asks'][0]['timestamp']
        self.sync_trade_clock()
        self.init_order_book()

    def init_order_book(self):
        self.order_book_transformer.transform_order_book(self.current_order_book)

    def sync_trade_clock(self):
        while self.trades[self.trade_count]['timestamp'] <= self.timestamp:
            self.trade_count += 1

    def make_step(self):
        reward = 0
        self.timestamp += 1
        if self.next_order_book['asks'][0]['timestamp'] == self.timestamp:
            self.current_order_book = self.next_order_book
            self.next_order_book = pk.load(self.order_book_file_handler)
            self.order_book_transformer.transform_order_book(ob.current_order_book)
        if self.trades[self.trade_count]['timestamp'] == self.timestamp:
            count = 0
            result_list = []
            while len(self.trades) > self.trade_count and self.trades[self.trade_count]['timestamp'] == self.timestamp:
                res = self.settle_trade(self.trades[self.trade_count], self.current_order_book)
                result_list.append(res)
                self.trade_count += 1
            self.state_space.update_state(result_list, self.current_order_book)
        if self.timestamp > self.trades[self.trade_count]['timestamp']:
            raise Exception()

    def settle_trade(self, trade, order_book):
        count = 0
        reward = 0
        total_amount = 0
        transaction_amount = 0
        transaction_price = 0
        trade_dict = {'buy':'asks', 'sell':'bids'}
        direction = trade_dict[trade['type']]
        try:
            while not order_book[direction][count]['my_order']:
                total_amount += float(order_book[direction][count]['amount'])
                count+=1
        except Exception as e:
            return {'amount':0, 'price':0, 'type':0}
        my_trade_amount = float(trade['amount']) - total_amountOrderBook
        my_order_amount = order_book[direction][count]['amount']
        if my_trade_amount > 0:
            if my_order_amount - my_trade_amount <= 0:
                transaction_amount = my_trade_amount
                transaction_price = order_book[direction][count]['price']
                self.order_book_transformer.delete_order(order_book[direction][count]['index'])
            else:
                transaction_amount = my_trade_amount
                transaction_price = order_book[direction][count]['price']
                self.order_book_transformer.delete_order(order_book[direction][count]['index'])
                self.order_book_transformer.add_order(order_book[direction][count]['price'], my_order_amount - my_trade_amount, trade['type'])
        return {'amount':transaction_amount, 'price':transaction_price, 'type':trade['type']}

class OrderBookTransformator(object):
    def __init__(self):
        self.alterations_list = []
        self.index = 0

    def insert_alteration(self, alteration, order_book):
        asks_book = order_book['asks']
        bids_book = order_book['bids']
        timestamp = order_book['asks'][0]['timestamp']
        if alteration['direction'] == 'buy':
            direction='asks'
            alteration_price = alteration['price']
            ask_prices = [ask['price'] for ask in asks_book]
            insertion_index = np.searchsorted(ask_prices, alteration_price)
            new_ask = {'price': alteration_price, 'timestamp':timestamp , 'amount':alteration['amount'], 'my_order':True, 'index':alteration['index']}
            order_book['asks'].insert(insertion_index, new_ask)
            order_book['asks'].pop()
        else:
            direction='bids'
            alteration_price = alteration['price']
            bid_prices = [bid['price'] for bid in bids_book]
            bid_prices.reverse()
            insertion_index = len(bid_prices) - np.searchsorted(bid_prices, alteration_price, side='right')
            new_bid = {'price': alteration_price, 'timestamp':timestamp , 'amount':alteration['amount'], 'my_order':True, 'index':alteration['index']}
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
        self.index += 1
        self.alterations_list.append({'price':price, 'amount':amount, 'direction':direction, 'index':self.index})

    def delete_order(self, index):
        for alt in self.alterations_list:
            if alt['index'] == index:
                self.alterations_list.remove(alt)
    
    def delete_orders(self):
        self.alterations_list = []

class ActionSpace(object):
    def __init__(self, config_file_path, config_name):
        self.config = ch.ConfigHelper(config_file_path, config_name)

    def network_action_to_alteration(self, price_action_vector, amount_action_vector, book, available_funds):
        calc_price = lambda x: 1 + (x - 0.5) * 2 / float(10)
        calc_amount = lambda x: x * 0.1
        ask_price_vector = price_action_vector[:self.config.order_price_scale_size]
        bid_price_vector = price_action_vector[self.config.order_price_scale_size:]
        ask_amount_vector = amount_action_vector[:self.config.order_amount_scale_size]
        bid_amount_vector = amount_action_vector[self.config.order_amount_scale_size:]
        ask_price_arg = ask_vector.argmax()
        bid_price_arg = bid_vector.argmax()
        current_ask_price = book['asks'][0]['price']
        current_bid_price = book['bids'][0]['price']
        suggested_ask_price = current_ask * calc_price(ask_arg / float(self.config.order_price_scale_size))
        suggested_bid_price = current_bid * calc_price(bid_arg / float(self.config.order_price_scale_size))
        ask_amount_arg = ask_amount_vector.argmax()
        bid_amount_arg = bid_amount_vector.argmax()
        suggested_ask_amount = (available_funds / current_ask) * calc_amount(ask_arg / float(self.config.order_amount_scale_size))
        suggested_bid_amount = (available_funds / current_bid) * calc_amount(bid_arg / float(self.config.order_amount_scale_size))
        return [(suggested_ask_price, suggested_ask_amount, 'buy'), (suggested_bid_price, suggested_bid_amount, 'sell')]

class MarketMakingGame(object):
    def __init__(self, config_file_path, config_name):
        self.order_book = OrderBook(config_file_path, config_name)
        self.action_space = ActionSpace(config_file_path, config_name)

    def get_state(self):
        return self.order_book.state_space.get_state()

    def make_action(self, price_action_vector, amount_action_vector):
        ask_order, bid_order = self.action_space.network_action_to_alteration(price_action_vector, amount_action_vector,
        self.order_book.current_order_book, self.order_book.state_space.available_funds)
        self.order_book.order_book_transformer.add_order()
        self.order_book.order_book_transformer.add_order()
        
        self.order_book.make_step()

    def get_total_reward(self):
        pass

    def is_episode_finished(self):
        pass

    def get_total_reward(self):
        pass

if __name__ == '__main__':
        ob = OrderBook('configs/btc_market_making_config.txt', 'MARKET_MAKING_CONFIG')
        [ob.make_step() for i in range(1000)]
        pdb.set_trace()
        # ob.order_book_transformer.add_order(4000.5, 1.1, 'sell')
        # print(ob.current_order_book)
        # ob.order_book_transformer.transform_order_book(ob.current_order_book)
        # t = {'amount': '0.5', 'timestamp': 1550567910, 'tid': 338912171, 'exchange': 'bitfinex', 'price': '3999.8', 'type': 'sell'}
        # res = ob.settle_trade(t, ob.current_order_book)
        # print(res)

# game.init()
# game.new_episode()
# state = game.get_state()
# reward = game.make_action(action)
# game.get_total_reward()
# done = game.is_episode_finished()
# score = game.get_total_reward()
# game.get_available_buttons_size()
# game.close()
