
import sys
import time

import pickle as pk
import bitfinex as bt

def main():
    count = 0
    while True:
        with open(sys.argv[1], 'ab') as fh1, open(sys.argv[2], 'ab') as fh2:
            try:
                pk.dump(bt.order_book(sys.argv[3]), fh1, protocol=4)
                if count % 10 == 0:
                    pk.dump(bt.trades(sys.argv[3]), fh2, protocol=4)
            except Exception as e:
                print(e)
            time.sleep(2)
            count += 1
            print(count)

if __name__ == '__main__':
    main()
