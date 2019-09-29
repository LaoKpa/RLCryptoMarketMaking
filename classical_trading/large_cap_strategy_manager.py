
import os
import sys
import time as tm

import basic_larg_cap_strategy as blcs

def main():
    symbol = ['tETHUSD', 'tXRPUSD', 'tEOSUSD', 'tLTCUSD', 'tIOTUSD', 'tXMRUSD', 'tNEOUSD']
    dollar_amount = 10
    req_spread_percntage = 0.003
    while True:
        print('Starting Market Making Strategy.')
        basic_large_cap_strategy = blcs.BasicLargeCapStrategy(symbol, dollar_amount)
        basic_large_cap_strategy.start_strategy_routine()
        print('Strategy Completed Successfully.')

if __name__ == '__main__':
    main()
