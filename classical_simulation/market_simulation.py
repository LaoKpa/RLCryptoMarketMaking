
import os
import imp
import math

import time as tm
import pickle as pk
import numpy as np

import market_simulator as mmg

CH = imp.load_source('config_helper', '../generic/config_helper.py')


class MarketSimulation(object):
    def __init__(self, config_file_path, config_name):
        config = CH.ConfigHelper(config_file_path, config_name)
        env = mmg.MarketMakingGame(config_file_path, config_name, config.order_book_base_path, config.num_of_buffer_samples, config.trades_file)
    

def main():
    config_file_path = '../configs/classical_simulation_config.txt'
    config_name = 'MARKET_MAKING_CONFIG'
    ms = MarketSimulation(config_file_path, config_name)

if __name__ == "__main__":
    main()
