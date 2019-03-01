
import sys
import time

import pickle as pk
import bitfinex as bt

def get_unified_trades(trades_file, output_file):
    count = 0
    time_stamp = 0
    full_trades_list = []
    with open(trades_file, 'rb') as fh:
        while True:
            try:
                trades_chunk = pk.load(fh)
                for trade in trades_chunk:
                    if time_stamp <= trade['timestamp']:
                        full_trades_list.append(trade)
                        time_stamp = trade['timestamp']
                        print(len(full_trades_list))
            except Exception as e:
                print(e)
                break
    with open(output_file, 'wb') as fh:
        pk.dump(full_trades_list, fh, protocol=4)
