
import sys
import time

import pickle as pk

ORDER_BOOK_LAG_RANGE = 10

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
    with open(order_book_file, 'rb') as fh, open(output_file, 'wb') as fho:
        while True:
            try:
                tmp_list_pre = []
                tmp_list_post = []
                for i in range(2 * ORDER_BOOK_LAG_RANGE):
                    order_book = pk.load(fh)
                    td = order_book['asks'][0]['timestamp'] - tmp_timestamp
                    tmp_timestamp = order_book['asks'][0]['timestamp']
                    if not td == 0 and tmp_timestamp > last_timestamp:
                        if i < ORDER_BOOK_LAG_RANGE:
                            tmp_list_pre.append(order_book)
                        else:
                            tmp_list_post.append(order_book)
                k = lambda x: x['asks'][0]['timestamp']
                tmp_list_pre.sort(key=k)
                last_timestamp = tmp_list_pre[-1]['asks'][0]['timestamp']
                for book in tmp_list_post:
                    if book['asks'][0]['timestamp'] < last_timestamp:
                        tmp_list_pre.append(book)
                tmp_list_pre.sort(key=k)
                for book in tmp_list_pre:
                    pk.dump(book, fho, protocol=4)
                count+=1
                print(count)
            except Exception as e:
                print(e)
                break

def get_sorted_order_book_list(order_book_file, output_file):
    count = 0
    tmp_timestamp = 0
    last_timestamp = 0
    with open(order_book_file, 'rb') as fh, open(output_file, 'wb') as fho:
        while True:
            try:
                tmp_list_pre = []
                tmp_list_post = []
                for i in range(2 * ORDER_BOOK_LAG_RANGE):
                    order_book = pk.load(fh)
                    td = order_book['asks'][0]['timestamp'] - tmp_timestamp
                    tmp_timestamp = order_book['asks'][0]['timestamp']
                    if not td == 0 and tmp_timestamp > last_timestamp:
                        if i < ORDER_BOOK_LAG_RANGE:
                            tmp_list_pre.append(order_book)
                        else:
                            tmp_list_post.append(order_book)
                k = lambda x: x['asks'][0]['timestamp']
                tmp_list_pre.sort(key=k)
                last_timestamp = tmp_list_pre[-1]['asks'][0]['timestamp']
                for book in tmp_list_post:
                    if book['asks'][0]['timestamp'] < last_timestamp:
                        tmp_list_pre.append(book)
                tmp_list_pre.sort(key=k)
                for book in tmp_list_pre:
                    pk.dump(book, fho, protocol=4)
                count+=1
                print(count)
            except Exception as e:
                print(e)
                break
def test_sorted_order_book(order_book_file):
    count = 0
    tmp_timestamp = 0
    last_timestamp = 0
    td_list = []
    ts_list = []
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
                print(order_book['asks'][0]['timestamp'])
                print(count)
            except Exception as e:
                print(e)
                break
        return td_list, ts_list
