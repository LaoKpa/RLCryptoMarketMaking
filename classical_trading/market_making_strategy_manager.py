
import sys
import time as tm

import pickle as pk
import websocket as wbs

import json
import threading
import time

import os
import tabulate as tb


import time as tm

import bitfinex as bt
import highest_spread_symbols as hss
import bitfinex_order_book_construction as bobc
import bitfinex_web_socket_auth as bwsa
import basic_market_making_strategy as bmms

def main():
    symbol = sys.argv[1]
    dollar_amount = 10
    req_spread_percntage = 0.002
    while True:
        print('Starting Market Making Strategy.')
        basic_market_making_strategy = bmms.BasicMarketMakingStrategy(symbol, req_spread_percntage, dollar_amount)
        basic_market_making_strategy.start_strategy_routine()
        print('Strategy Completed Successfully.')
        basic_market_making_strategy.release_resources()
        print('Releasing Resources.')

if __name__ == '__main__':
    main()
