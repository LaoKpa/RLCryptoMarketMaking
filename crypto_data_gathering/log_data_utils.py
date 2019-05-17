
import sys
import time

import pickle as pk

import imp
import tensorflow as tf

CH = imp.load_source('config_helper', '../generic/config_helper.py')

ORDER_BOOK_LAG_RANGE = 1000

def get_unified_trades(trades_file, output_file):
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

def get_sorted_order_book_list(order_book_file, output_file):
    count = 0
    tmp_timestamp = 0
    last_timestamp = 0
    tmp_list_pre = []
    tmp_list_post = []
    extract_timestamp = lambda x: x['asks'][0]['timestamp']
    uniqify = lambda d, g: [{g(i):i for i in d}[k] for k in sorted(list(set([g(l) for l in d])))]
    print('Generating Normaized Orderbook Dataset...')
    with open(order_book_file, 'rb') as fh, open(output_file, 'wb') as fho:
        while True:
            try:
                if count == 0:
                    for i in range(2 * ORDER_BOOK_LAG_RANGE):
                        order_book = pk.load(fh)
                        td = order_book['asks'][0]['timestamp'] - tmp_timestamp
                        tmp_timestamp = order_book['asks'][0]['timestamp']
                        if not td == 0:
                            if i < ORDER_BOOK_LAG_RANGE:
                                tmp_list_pre.append(order_book)
                            else:
                                tmp_list_post.append(order_book)
                else:
                    tmp_timestamp = tmp_list_post[-1]['asks'][0]['timestamp']
                    first_timestamp_post = tmp_list_post[0]['asks'][0]['timestamp']
                    last_timestamp_pre = tmp_list_pre[-1]['asks'][0]['timestamp']
                    if last_timestamp_pre == first_timestamp_post:
                        tmp_list_post = tmp_list_post[1:]
                    tmp_list_pre = tmp_list_post
                    tmp_list_post = []
                    for i in range(ORDER_BOOK_LAG_RANGE):
                        order_book = pk.load(fh)
                        td = order_book['asks'][0]['timestamp'] - tmp_timestamp
                        tmp_timestamp = order_book['asks'][0]['timestamp']
                        if not td == 0:
                            tmp_list_post.append(order_book)

                k = lambda x: x['asks'][0]['timestamp']
                tmp_list_pre.sort(key=k)
                last_timestamp = tmp_list_pre[-1]['asks'][0]['timestamp']
                for book in tmp_list_post:
                    if book['asks'][0]['timestamp'] < last_timestamp:
                        tmp_list_pre.append(book)
                        tmp_list_post.remove(book)
                tmp_list_pre.sort(key=k)
                tmp_list_post.sort(key=k)
                tmp_list_pre = uniqify(tmp_list_pre, extract_timestamp)
                tmp_list_post = uniqify(tmp_list_post, extract_timestamp)
                for book in tmp_list_pre:
                    pk.dump(book, fho, protocol=4)
                count+=1
                print('Progress Count: {0}'.format(count), end='\r', flush=True)
            except Exception as e:
                break

def test_sorted_order_book(order_book_file):
    count = 0
    tmp_timestamp = 0
    last_timestamp = 0
    td_list = []
    ts_list = []
    print('Testing Normalized Dataset Generation...')
    with open(order_book_file, 'rb') as fh:
        while True:
            try:
                tmp_list_pre = []
                tmp_list_post = []
                order_book = pk.load(fh)
                td = order_book['asks'][0]['timestamp'] - tmp_timestamp
                tmp_timestamp = order_book['asks'][0]['timestamp']
                ts_list.append(tmp_timestamp)
                td_list.append(td)
                count+=1
                print('Timestamp: {0} | Count: {1}'.format(order_book['asks'][0]['timestamp'], count), end='\r', flush=True)
            except Exception as e:
                break
        return td_list, ts_list, count

def main():
    config = CH.ConfigHelper('../configs/normalize_order_book_data_config.txt', 'ORDER_BOOK_DATA_NORMALIZATION_CONFIG')
    get_sorted_order_book_list(config.order_book_file, config.normalized_order_book_file)
    td_list, ts_list, num_of_samples = test_sorted_order_book(config.normalized_order_book_file)
    min_td = min(td_list)
    avg_td = sum(td_list[1:])/float(len(td_list))
    if min_td > 0 and avg_td < config.predicted_td_avg:
        print('NORMALIZED ORDER BOOK DATASET GENERATED OK!')
        print('Number of samples: {0}.'.format(num_of_samples))
    else:
        print('FAILD TO NORMALIZE ORDER BOOK DATASET GENERATED!')
        print('Stats: avg td = {0} | min td = {1}'.format(avg_td, min_td))

if __name__ == '__main__':
    main()
