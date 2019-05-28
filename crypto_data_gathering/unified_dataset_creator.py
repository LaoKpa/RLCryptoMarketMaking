import sys
import time

import pickle as pk

import imp
import tensorflow as tf
import numpy as np

import convert_ob_to_efficient_dataset as obto
import convert_tr_to_efficient_dataset as trto
import devide_ob_dataset as obdev
import log_data_utils as ldu


order_book_file = /media/lavi/FourTera/RLMM/zec/ob_zec.bin
normalized_order_book_file = /media/lavi/FourTera/RLMM/zec/ob_zec_normalized.bin
predicted_td_avg = 5.0

'/home/lavi/Documents/RLMM/data_sets/zec/ob_zec_normalized.bin'
'/home/lavi/Documents/RLMM/data_sets/zec/ob_zec_normalized_parted'
20



def filter_order_books(order_book_file, normalized_order_book_file, predicted_td_avg):
    ldu.get_sorted_order_book_list(order_book_file, normalized_order_book_file)
    td_list, ts_list, num_of_samples = ldu.test_sorted_order_book(normalized_order_book_file)
    min_td = min(td_list)
    avg_td = sum(td_list[1:])/float(len(td_list))
    if min_td > 0 and avg_td < predicted_td_avg:
        print('NORMALIZED ORDER BOOK DATASET GENERATED OK!')
        print('Number of samples: {0}.'.format(num_of_samples))
    else:
        print('FAILD TO NORMALIZE ORDER BOOK DATASET GENERATED!')
        print('Stats: avg td = {0} | min td = {1}'.format(avg_td, min_td))

def main():
    # Orderbook preprocessing
    filter_order_books(order_book_file, normalized_order_book_file, normalized_order_book_file, predicted_td_avg)
    obdev.generic_data_manipulation_function(order_book_file, order_book_base_path, number_of_parts)
    obto.save_parted_datasets_numpy(order_book_base_path_in, order_book_base_path_out, num_of_parts)
    # Trades preprocessing
    get_unified_trades(trades_file, output_file)

if __name__ == '__main__':
    main()
