
from __future__ import absolute_import
import requests
import json
import base64
import hmac
import hashlib
import time

PROTOCOL = "https"
HOST = "api.bitfinex.com"
VERSION = "v1"

PATH_SYMBOLS = "symbols"
PATH_TICKER = "ticker/%s"
PATH_TODAY = "today/%s"
PATH_STATS = "stats/%s"
PATH_LENDBOOK = "lendbook/%s"
PATH_ORDERBOOK = "book/%s"

# HTTP request timeout in seconds
TIMEOUT = 5.0

class TradeClient:
    def __init__(self, key, secret):
        self.URL = "{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)
        self.KEY = key
        self.SECRET = secret
        pass

    @property
    def _nonce(self):
        return str(time.time() * 1000000)

    def _sign_payload(self, payload):
        j = json.dumps(payload)
        data = base64.standard_b64encode(j.encode('utf8'))
        h = hmac.new(self.SECRET.encode('utf8'), data, hashlib.sha384)
        signature = h.hexdigest()
        return {
            "X-BFX-APIKEY": self.KEY,
            "X-BFX-SIGNATURE": signature,
            "X-BFX-PAYLOAD": data
        }

    def place_order(self, amount, price, side, ord_type, symbol, exchange='bitfinex'):
        payload = {

            "request": "/v1/order/new",
            "nonce": self._nonce,
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "exchange": exchange,
            "side": side,
            "type": ord_type

        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/new", headers=signed_payload, verify=True)
        json_resp = r.json()
        try:
            json_resp['order_id']
        except:
            return json_resp['message']
        return json_resp

    def replace_order(self, order_id, symbol, amount, price, side, ord_type, exchange='bitfinex'):
        payload = {
            "request": "/v1/order/cancel/replace",
            "nonce": self._nonce,
            "order_id": order_id,
            "symbol": symbol,
            "amount": amount,
            "price": price,
            "exchange": exchange,
            "side": side,
            "type": ord_type
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel/replace", headers=signed_payload, verify=True)
        json_resp = r.json()
        try:
            json_resp['order_id']
        except:
            return json_resp['message']
        return json_resp

    def delete_order(self, order_id):
        payload = {
            "request": "/v1/order/cancel",
            "nonce": self._nonce,
            "order_id": order_id
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel", headers=signed_payload, verify=True)
        json_resp = r.json()
        try:
            json_resp['avg_excution_price']
        except:
            return json_resp['message']
        return json_resp

    def delete_all_orders(self):
        payload = {
            "request": "/v1/order/cancel/all",
            "nonce": self._nonce,
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/cancel/all", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def status_order(self, order_id):
        payload = {
            "request": "/v1/order/status",
            "nonce": self._nonce,
            "order_id": order_id
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/order/status", headers=signed_payload, verify=True)
        json_resp = r.json()
        try:
            json_resp['avg_execution_price']
        except:
            return json_resp['message']

        return json_resp

    def active_orders(self):
        payload = {
            "request": "/v1/orders",
            "nonce": self._nonce
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/orders", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def active_positions(self):
        payload = {
            "request": "/v1/positions",
            "nonce": self._nonce
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/positions", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def claim_position(self, position_id):
        payload = {
            "request": "/v1/position/claim",
            "nonce": self._nonce,
            "position_id": position_id
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/position/claim", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def past_trades(self, symbol, timestamp=0):
        payload = {
            "request": "/v1/mytrades",
            "nonce": self._nonce,
            "symbol": symbol,
            "timestamp": timestamp
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/mytrades", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def place_offer(self, currency, amount, rate, period, direction):
        payload = {
            "request": "/v1/offer/new",
            "nonce": self._nonce,
            "currency": currency,
            "amount": amount,
            "rate": rate,
            "period": period,
            "direction": direction
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offer/new", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def cancel_offer(self, offer_id):
        payload = {
            "request": "/v1/offer/cancel",
            "nonce": self._nonce,
            "offer_id": offer_id
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offer/cancel", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def status_offer(self, offer_id):
        payload = {
            "request": "/v1/offer/status",
            "nonce": self._nonce,
            "offer_id": offer_id
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offer/status", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def active_offers(self):
        payload = {
            "request": "/v1/offers",
            "nonce": self._nonce
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/offers", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def balances(self):
        payload = {
            "request": "/v1/balances",
            "nonce": self._nonce
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/balances", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp

    def margin_infos(self):
        payload = {
            "request": "/v1/margin_infos",
            "nonce": self._nonce
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/margin_infos", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp        

    def history(self, currency, since=0, until=9999999999, limit=500, wallet='exchange'):
        payload = {
            "request": "/v1/history",
            "nonce": self._nonce,
            "currency": currency,
            "since": since,
            "until": until,
            "limit": limit,
            "wallet": wallet
        }
        signed_payload = self._sign_payload(payload)
        r = requests.post(self.URL + "/history", headers=signed_payload, verify=True)
        json_resp = r.json()
        return json_resp
