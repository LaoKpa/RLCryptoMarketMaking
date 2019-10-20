
import os
import imp
import math

import time as tm
import pickle as pk
import numpy as np

import market_making_game as mmg

CH = imp.load_source('config_helper', '../generic/config_helper.py')

def main():
    config_file_path = '../configs/btc_market_making_config.txt'
    config_name = 'MARKET_MAKING_CONFIG'
    config = CH.ConfigHelper(config_file_path, config_name)
    dc = get_data_conveyer(config.order_book_base_path)
    with open(config.trades_file, 'rb') as fh:
        trades = np.load(fh)
    env = mmg.MarketMakingGame(config_file_path, config_name, dc, trades)

if __name__ == "__main__":
    main()
