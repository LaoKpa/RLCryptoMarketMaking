
import sys
import time

import pickle as pk

import imp
import tensorflow as tf



def generic_data_manipulation_function(order_book_file, order_book_base_path, number_of_parts):
    count = 0
    with open(order_book_file, 'rb') as fh:
        while True:
            try:
                order_book = pk.load(fh)
                count+=1
                print('Count: {0}'.format(count), end='\r', flush=True)
            except Exception as e:
                break
    num_of_samples = count
    file_count = 0
    with open(order_book_file, 'rb') as fh:
        while True:
            try:
                sample_list = []
                for i in range(num_of_samples // number_of_parts):
                    order_book = pk.load(fh)
                    sample_list.append(order_book)
                    count+=1
                    print('Count: {0} | {1}'.format(i, file_count), end='\r', flush=True)
                with open('{0}_{1}.bin'.format(order_book_base_path, file_count), 'wb') as fho:
                    pk.dump(sample_list, fho, protocol=4)
                    file_count += 1
            except Exception as e:
                print(e)
                break

def main():
    print('\nTotal sample num: {0}.'.format(generic_data_manipulation_function\
        ('/home/lavi/Documents/RLMM/data_sets/zec/ob_zec_normalized.bin',\
            '/home/lavi/Documents/RLMM/data_sets/zec/ob_zec_normalized_parted', 20)))

if __name__ == '__main__':
    main()
