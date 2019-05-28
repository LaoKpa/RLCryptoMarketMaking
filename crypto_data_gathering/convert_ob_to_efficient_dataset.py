
import sys
import time

import pickle as pk

import imp
import tensorflow as tf
import numpy as np

KEYS_ORDER = ['timestamp', 'price', 'amount']

def generic_data_manipulation_function(order_book_base_path_in, order_book_base_path_out, file_count):
    count = 0
    data = []
    with open('{0}_{1}.bin'.format(order_book_base_path_in, file_count), 'rb') as fh:
        order_books = pk.load(fh)
        for order_book in order_books:
            data.append([[[ float(l[k]) for k in KEYS_ORDER]+[0.0] for l in order_book[t]] for t in ['asks', 'bids']])
            print('Count: {0} | {1}'.format(count, file_count), end='\r', flush=True)
            count+=1

    with open('{0}_{1}.bin'.format(order_book_base_path_out, file_count), 'wb') as fho:
        np.save(fho, np.array(data))

def save_parted_datasets_numpy(order_book_base_path_in, order_book_base_path_out, num_of_parts):
    for i in range(num_of_parts):
        generic_data_manipulation_function(order_book_base_path_in, order_book_base_path_out, i)

def main():
    save_parted_datasets_numpy('/home/lavi/Documents/RLMM/data_sets/zec/ob_zec_normalized_parted',\
        '/home/lavi/Documents/RLMM/data_sets/zec/ob_zec_normalized_parted_numpy', 20)

if __name__ == '__main__':
    main()
