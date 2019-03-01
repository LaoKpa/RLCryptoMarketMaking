
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
PATH_TRADES = "trades/%s"

# HTTP request timeout in seconds
TIMEOUT = 5.0

def _convert_to_floats(data):
    for key, value in data.items():
        data[key] = float(value)
    return data

def _build_parameters(parameters):
    keys = list(parameters.keys())
    keys.sort()
    return '&'.join(["%s=%s" % (k, parameters[k]) for k in keys])

def _get(url):
    return requests.get(url, timeout=TIMEOUT).json()

def server():
    return u"{0:s}://{1:s}/{2:s}".format(PROTOCOL, HOST, VERSION)


def build_url(path, path_arg=None, parameters=None):
    url = "%s/%s" % (server(), path)
    if path_arg:
        url = url % (path_arg)
    if parameters:
        url = "%s?%s" % (url, _build_parameters(parameters))
    return url


def symbols():
    return _get(build_url(PATH_SYMBOLS))


def ticker(symbol):
    data = _get(build_url(PATH_TICKER, (symbol)))
    return _convert_to_floats(data)


def today(symbol):
    data = _get(build_url(PATH_TODAY, (symbol)))
    return _convert_to_floats(data)


def stats(symbol):
    data = _get(build_url(PATH_STATS, (symbol)))
    for period in data:
        for key, value in period.items():
            if key == 'period':
                new_value = int(value)
            elif key == 'volume':
                new_value = float(value)
            period[key] = new_value
    return data


def lendbook(currency, parameters=None):
    data = _get(build_url(PATH_LENDBOOK, path_arg=currency, parameters=parameters))
    for lend_type in data.keys():
        for lend in data[lend_type]:
            for key, value in lend.items():
                if key in ['rate', 'amount', 'timestamp']:
                    new_value = float(value)
                elif key == 'period':
                    new_value = int(value)
                elif key == 'frr':
                    new_value = value == 'Yes'
                lend[key] = new_value
    return data

def trades(symbol, parameters=None):
    data = _get(build_url(PATH_TRADES, path_arg=symbol, parameters=parameters))
    # for type_ in data.keys():
    #     for list_ in data[type_]:
    #         for key, value in list_.items():
    #             list_[key] = float(value)
    return data

def order_book(symbol, parameters=None):
    data = _get(build_url(PATH_ORDERBOOK, path_arg=symbol, parameters=parameters))
    for type_ in data.keys():
        for list_ in data[type_]:
            for key, value in list_.items():
                list_[key] = float(value)
    return data
