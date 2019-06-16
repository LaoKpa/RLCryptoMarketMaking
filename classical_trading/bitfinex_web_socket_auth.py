
import hmac
import hashlib
import time
import json 

import websocket as wbs

BITFINEX_KEY = "N1bQYgTEzuDvzwYcpFXhiv1So0Df1IhoVj8wWQvczqT"
BITFINEX_SECRET = "L5LUl8e65GRsxMd28naxTL5dITticeD6mKTSloUDcG3"
def get_auth():
    nonce = int(time.time() * 1000000)
    auth_payload = 'AUTH{}'.format(nonce)
    signature = hmac.new(BITFINEX_SECRET.encode(), msg = auth_payload.encode(), digestmod = hashlib.sha384).hexdigest()

    payload = {
    'apiKey': BITFINEX_KEY,
    'event': 'auth',
    'authPayload': auth_payload,
    'authNonce': nonce,
    'authSig': signature
    }
    return payload

# ws = wbs.WebSocketApp('wss://api-pub.bitfinex.com/ws/2')
# print(ws.send(json.dumps(payload)))
