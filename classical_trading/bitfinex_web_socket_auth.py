
import hmac
import hashlib
import time
import json 

import threading
import random as rnd
import websocket as wbs

from pprint import pprint

BITFINEX_KEY = 'N1bQYgTEzuDvzwYcpFXhiv1So0Df1IhoVj8wWQvczqT'
BITFINEX_SECRET = 'L5LUl8e65GRsxMd28naxTL5dITticeD6mKTSloUDcG3'
NONCE_FACTOR = 1000000
BITFINEX_API_URL = 'wss://api.bitfinex.com/ws/2'
BITFINEX_HEART_BEAT = '[0,"hb"]'

def verify_response(resp_stack, lam):
	while True: 
		for q in resp_stack:
			if lam(q):
				resp_stack.remove(q)
				return (True, q)

class Order(object):
	def __init__(self):
		self.order_id
		self.order_cid
		self.chanle_id
		self.symbol
		self.amount
		self.price
		self.exec_amount
		self.exec_price
		self.is_active
		self.order_type
		self.fee
		self.fee_currnecy
		self.maker
		self.time_stamp

class OrderStreamParser(object):
	def __init__(self, order_request_responsoe):
		self.chanle_id = order_request_responsoe[0]
		self.event_string = order_request_responsoe[1]
		if order_request_responsoe[2] == []:
			return
		self.order_id = order_request_responsoe[2][0][0]
		self.order_gid = order_request_responsoe[2][0][1]
		self.order_cid = order_request_responsoe[2][0][2]
		self.symbol = order_request_responsoe[2][0][3]
		self.mts_create = order_request_responsoe[2][0][4]
		self.mts_update = order_request_responsoe[2][0][5]
		self.amount = order_request_responsoe[2][0][6]
		self.amount_orig = order_request_responsoe[2][0][7]
		self.type = order_request_responsoe[2][0][8]
		self.type_prev = order_request_responsoe[2][0][9]
		self.mts_tif = order_request_responsoe[2][0][10]
		self.flags = order_request_responsoe[2][0][12]
		self.status = order_request_responsoe[2][0][13]
		self.status_dictionaty = self.parse_update_status(self.status)
		self.price = order_request_responsoe[2][0][16]
		self.price_avg = order_request_responsoe[2][0][17]
		self.price_aux_limit = order_request_responsoe[2][0][18]
		self.notify = order_request_responsoe[2][0][22]
		self.hidden = order_request_responsoe[2][0][23]
		self.placed_id = order_request_responsoe[2][0][24]
		self.routing = order_request_responsoe[2][0][27]

	def parse_update_status(self, order_status_string):
		def parse_splitted_order_status(order_status):
			splitted_order_status = order_status.replace(' ', '').split('@')
			executed_amount = float(splitted_order_status[1].split('(')[1].split(')')[0])
			executed_price = float(splitted_order_status[1].split('(')[0])
			order_status_status = splitted_order_status[0]
			return executed_amount, executed_price, order_status_status
		if 'was' in order_status_string:
			order_error, splitted_order_status = order_status_string.replace(' ', '').split('was:')
			executed_amount, executed_price, order_status_status = parse_splitted_order_status(splitted_order_status)
			return {'order_error':order_error, 'executed_amount':executed_amount, 'executed_price':executed_price, 'order_status_status':order_status_status}
		elif '@' in order_status_string:
			executed_amount, executed_price, order_status_status = parse_splitted_order_status(order_status_string)
			return {'executed_amount':executed_amount, 'executed_price':executed_price, 'order_status_status':order_status_status}
		else:
			splitted_order_status = order_status_string.replace(' ', '')
			return {'order_status_status':splitted_order_status}

class TradeUpdateParser(object):
	def __init__(self, order_request_responsoe):
		self.chanle_id = order_request_responsoe[0]
		self.event_string = order_request_responsoe[1]
		self.trade_id = order_request_responsoe[2][0]
		self.symbol = order_request_responsoe[2][1]
		self.time_stamp = order_request_responsoe[2][2]
		self.order_id = order_request_responsoe[2][3]
		self.exec_amount = order_request_responsoe[2][4]
		self.exec_price = order_request_responsoe[2][5]
		self.orderer_type = order_request_responsoe[2][6]
		self.order_price = order_request_responsoe[2][7]
		self.maker = order_request_responsoe[2][8]
		self.fee = order_request_responsoe[2][9]
		self.fee_currnecy = order_request_responsoe[2][10]

class TradeEventParser(object):
	def __init__(self, order_request_responsoe):
		self.chanle_id = order_request_responsoe[0]
		self.event_string = order_request_responsoe[1]
		self.trade_id = order_request_responsoe[2][0]
		self.symbol = order_request_responsoe[2][1]
		self.time_stamp = order_request_responsoe[2][2]
		self.order_id = order_request_responsoe[2][3]
		self.exec_amount = order_request_responsoe[2][4]
		self.exec_price = order_request_responsoe[2][5]
		self.orderer_type = order_request_responsoe[2][6]
		self.order_price = order_request_responsoe[2][7]
		self.maker = order_request_responsoe[2][8]

class OrderRequestParser(object):
	def __init__(self, order_request_responsoe):
		self.request_string = order_request_responsoe[2][1]
		self.order_id = order_request_responsoe[2][4][0]
		self.order_cid = order_request_responsoe[2][4][2]
		self.symbol = order_request_responsoe[2][4][3]
		self.amount = order_request_responsoe[2][4][6]
		self.type = order_request_responsoe[2][4][8]
		self.is_active = order_request_responsoe[2][4][13]
		self.price = order_request_responsoe[2][4][16]
		self.is_successful = order_request_responsoe[2][6]
		self.message = order_request_responsoe[2][7]

class OrderConfirmationParser(object):
	def __init__(self, order_confirmation_responsoe):
		self.request_string = order_confirmation_responsoe[1]
		self.order_id = order_confirmation_responsoe[2][0]
		self.order_cid = order_confirmation_responsoe[2][2]
		self.symbol = order_confirmation_responsoe[2][3]
		self.amount = order_confirmation_responsoe[2][6]
		self.type = order_confirmation_responsoe[2][8]
		self.is_active = order_confirmation_responsoe[2][13]
		self.price = order_confirmation_responsoe[2][16]

class AuthenticationParser(object):
	def __init__(self, auth_response):
		self.status = auth_response['status']
		self.chan_id = auth_response['chanId']
		self.user_id = auth_response['userId']
		self.auth_id = auth_response['auth_id']
		self.is_authenticated = self.status == 'OK'

class ResponseObjectFactory(object):
	def __init__(self):
		pass
	def get_response_object(self, resp):
		if type(resp) is dict:
			if 'event' in resp.keys():
				if resp['event'] == 'auth':
					return AuthenticationParser(resp)
		elif type(resp) is list:
			if 'on' in resp:
				return OrderConfirmationParser(resp)
			elif 'oc' in resp:
				return OrderConfirmationParser(resp)
			elif 'ou' in resp:
				return OrderConfirmationParser(resp)
			elif 'n' in resp:
				return OrderRequestParser(resp)
			elif 'te' in resp:
				return TradeEventParser(resp)
			elif 'tu' in resp:
				return TradeUpdateParser(resp)
			elif 'os' in resp:
				return OrderStreamParser(resp)

class ContinuousIDTable(object):
	def __init__(self):
		self.cid_table = []
		self.cid_count = 0
		self.current_cid = 0
		self.seed = rnd.randint(0, 10**8)

	def get_next_cid(self):
		cid = self.seed + self.cid_count
		self.cid_table.append(cid)
		self.current_cid = cid
		self.cid_count += 1
		return cid

class BitfinexWebSocketClient(threading.Thread):
	def __init__(self, bitfinex_key, bitfinex_secret, nonce_factor, api_url):
		threading.Thread.__init__(self)
		self.bitfinex_key = bitfinex_key
		self.bitfinex_secret = bitfinex_secret
		self.nonce_factor = nonce_factor
		self.api_url = api_url
		self.websocket_connection = wbs.create_connection(self.api_url)
		self.cid_generator = ContinuousIDTable()
		self.response_object_factory = ResponseObjectFactory()
		self.order_confirmation_stack = []
		self.order_request_stack = []
		self.authentication_stack = []
		self.approved_order_confirmation_stack = {}
		self.trade_event_stack = []
		self.trade_update_stack = []
		self.order_stream_stack = []

	def print_stack_stats(self):
		print('order_confirmation_stack length: {0}'.format(len(self.order_confirmation_stack)))
		print('order_request_stack length: {0}'.format(len(self.order_request_stack)))
		print('authentication_stack length: {0}'.format(len(self.authentication_stack)))
		print('approved_order_confirmation_stack length: {0}'.format(len(self.approved_order_confirmation_stack)))
		print('trade_event_stack length: {0}'.format(len(self.trade_event_stack)))
		print('trade_update_stack length: {0}'.format(len(self.trade_update_stack)))
		print('order_stream_stack length: {0}'.format(len(self.order_stream_stack)))

	def get_auth_payload(self):
		nonce = int(time.time() * self.nonce_factor)
		auth_payload = 'AUTH{}'.format(nonce)
		signature = hmac.new(self.bitfinex_secret.encode(), msg = auth_payload.encode(), digestmod = hashlib.sha384).hexdigest()
		payload = {
		'apiKey': self.bitfinex_key,
		'event': 'auth',
		'authPayload': auth_payload,
		'authNonce': nonce,
		'authSig': signature}
		return payload

	def authenticate(self):
		auth_payload = self.get_auth_payload()
		self.websocket_connection.send(json.dumps(auth_payload))
		is_successful, _ = verify_response(self.authentication_stack, lambda q: q.is_authenticated)
		return is_successful

	def prepare_new_order_req(self, cid_num, symbol, amount, price):
		req_dict = [0, 'on', None, {'gid': 1, 'cid': cid_num, 'type': 'LIMIT', 'symbol': symbol, 'amount': str(amount), 'price': str(price)}]
		return json.dumps(req_dict)
	
	def verify_order_response(self, query):
		self.websocket_connection.send(query)
		self.order_cid_lambda = lambda q: q.order_cid == self.cid_generator.current_cid
		request_success, _ = verify_response(self.order_request_stack, self.order_cid_lambda)
		confirmation_success, order_confirmation = verify_response(self.order_confirmation_stack, self.order_cid_lambda)
		return (request_success and confirmation_success, order_confirmation)

	def place_new_order(self, symbol, amount, price):
		new_order_query = self.prepare_new_order_req(self.cid_generator.get_next_cid(), symbol, amount, price)
		request_confirmation_success, order_confirmation = self.verify_order_response(new_order_query)
		self.approved_order_confirmation_stack[order_confirmation.order_id] = order_confirmation
		return request_confirmation_success

	def update_order(self, ord_id, amount, price):
		update_order_query = [0, 'ou', None, {'id': ord_id, 'amount': str(amount), 'price': str(price)}]
		request_confirmation_success, order_confirmation = self.verify_order_response(json.dumps(update_order_query))
		self.approved_order_confirmation_stack[order_confirmation.order_id] = order_confirmation
		return request_confirmation_success

	def cancle_order(self, ord_id):
		cancle_order_query = [0, "oc", None, {"id":ord_id}]
		request_confirmation_success, order_confirmation = self.verify_order_response(json.dumps(cancle_order_query))
		self.approved_order_confirmation_stack.pop(order_confirmation.order_id)
		return request_confirmation_success
	
	def process_trade(self, trade_update_resp):
		for k in self.approved_order_confirmation_stack.keys():
			if trade_update_resp.order_id == k:
				self.approved_order_confirmation_stack.pop(k)

	def process_order_stream(self, order_stream_resp):
		pass

	def run(self):
		while True:
			resp = self.websocket_connection.recv()
			if not resp == BITFINEX_HEART_BEAT:
				resp_python_object = json.loads(resp)
				resp_factory_object = self.response_object_factory.get_response_object(resp_python_object)
				if type(resp_factory_object) is OrderConfirmationParser:
					self.order_confirmation_stack.append(resp_factory_object)
				elif type(resp_factory_object) is OrderRequestParser:
					self.order_request_stack.append(resp_factory_object)
				elif type(resp_factory_object) is AuthenticationParser:
					self.authentication_stack.append(resp_factory_object)
				elif type(resp_factory_object) is TradeEventParser:
					self.trade_event_stack.append(resp_factory_object)
				elif type(resp_factory_object) is TradeUpdateParser:
					self.trade_update_stack.append(resp_factory_object)
				elif type(resp_factory_object) is OrderStreamParser:
					self.order_stream_stack.append(resp_factory_object)

def main():
	bwsc = BitfinexWebSocketClient(BITFINEX_KEY, BITFINEX_SECRET, NONCE_FACTOR, BITFINEX_API_URL)
	bwsc.start()
	return bwsc
