
import sys
import time

import pickle as pk

import imp
import tensorflow as tf
import numpy as np

KEYS_ORDER = ['timestamp', 'price', 'amount', 'type', 'tid']

def trade_encode_helper(trade_parameter):
	if trade_parameter in ['sell', 'buy']:
		return {'sell':0, 'buy':1}[trade_parameter]
	return trade_parameter

def generic_data_manipulation_function(order_book_base_path_in, order_book_base_path_out):
    count = 0
    data = []
    with open(order_book_base_path_in, 'rb') as fh:
        trades = pk.load(fh)
        for trade in trades:
            data.append([float(trade_encode_helper(trade[k])) for k in KEYS_ORDER])
        #     import pdb; pdb.set_trace()
            print('Count: {0}.'.format(count), end='\r', flush=True)
            count+=1

    with open(order_book_base_path_out, 'wb') as fho:
        np.save(fho, np.array(data))

def main():
    generic_data_manipulation_function('/home/lavi/Documents/RLMM/data_sets/zec/tr_zec_unified.bin',\
        '/home/lavi/Documents/RLMM/data_sets/zec/tr_zec_unified_numpy.bin')

if __name__ == '__main__':
    main()
