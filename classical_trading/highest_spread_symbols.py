
import time as tm
import requests as req

import bitfinex as btf

SYMBOL_INDEX = 0

BID_INDEX = 1
ASK_INDEX = 3
VOLUME_INDEX = 8

def get_all_tickers():
	symbols = req.get('https://api-pub.bitfinex.com/v2/tickers?symbols=ALL').json()
	return symbols

def get_symbols_details():
	symbols_details = req.get('https://api.bitfinex.com/v1/symbols_details').json()
	return symbols_details

def get_sorted_symbols(relative_spread_treshold):
	symbol_list = []
	symbols = get_all_tickers()
	details = get_symbols_details()
	get_details = lambda sym: [p for p in details if p['pair'].upper()==sym[SYMBOL_INDEX][1:]][0]
	for s in symbols:
		if s[SYMBOL_INDEX][0] == 't':
			symbol_details = get_details(s)
			price = (s[ASK_INDEX] + s[BID_INDEX]) / 2.0
			spread  = s[ASK_INDEX] - s[BID_INDEX]
			relative_spread = spread / price
			if relative_spread > relative_spread_treshold:
				symbol_list.append({'pair':s[SYMBOL_INDEX], 'spread':relative_spread, 'volume':s[VOLUME_INDEX], 'price':price,
				'volume_usd':s[VOLUME_INDEX] * price, 'margin':symbol_details['margin']})
	symbol_list.sort(key=lambda k: -k['volume_usd'])
	return symbol_list
