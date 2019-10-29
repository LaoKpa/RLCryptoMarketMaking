
import os
import sys
import imp
import math

import time as tm
import pickle as pk
import numpy as np

import market_simulator as mmg

CH = imp.load_source('config_helper', '../generic/config_helper.py')

class 

class MarketSimulation(object):
    def __init__(self, config_file_path, config_name):
        config = CH.ConfigHelper(config_file_path, config_name)
        self.env = mmg.MarketMakingGame(config_file_path, config_name, config.order_book_base_path, config.num_of_buffer_samples, config.trades_file)

    def start_simulation(self, pre_strategy_cycles_num, strategy):
        history = []
        for _ in range(pre_strategy_cycles_num):
            self.env.make_empty_action()
            history.append(self.env.get_status())
        while True:
            price, amount = strategy.run(history)
            self.env.place_limit_order(price, amount)
            self.env.make_empty_action()
            history.append(self.env.get_status())

def main():
    config_file_path = sys.argv[1]
    config_name = 'MARKET_MAKING_CONFIG'
    ms = MarketSimulation(config_file_path, config_name)

if __name__ == "__main__":
    main()
