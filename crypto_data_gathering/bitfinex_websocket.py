

import sys
import time

import pickle as pk
import websocket as wbs

def wbs_on_message(event, fh):
    print(event)
    pk.dump(event, fh, protocol=4)

def main():
    count = 0
    with open(sys.argv[1], 'ab') as fh:
        try:
            ws = wbs.WebSocketApp('wss://api-pub.bitfinex.com/ws/2')
            ws.on_open = lambda self: self.send('{ "event": "subscribe", "channel": "trades", "symbol": "' + sys.argv[2] + '"}')
            ws.on_message = lambda self, evt: wbs_on_message(evt, fh)
            ws.run_forever()
        except Exception as e:
            print(e)

if __name__ == '__main__':
    main()
