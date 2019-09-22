
import hmac
import hashlib
import time
import json 

import threading
import random as rnd
import websocket as wbs

from pprint import pprint

from bitfinex_web_socket_structures import *

import logging
logging.basicConfig(filename='basic_market_making.log',level=logging.DEBUG)

BITFINEX_KEY = 'N1bQYgTEzuDvzwYcpFXhiv1So0Df1IhoVj8wWQvczqT'
BITFINEX_SECRET = 'L5LUl8e65GRsxMd28naxTL5dITticeD6mKTSloUDcG3'
NONCE_FACTOR = 1000000
BITFINEX_API_URL = 'wss://api.bitfinex.com/ws/2'
BITFINEX_HEART_BEAT = '[0,"hb"]'

GLOBAL_VERIFICATION_LOCK = True

def verify_response(resp_stack, lam):
	while True:
		for q in resp_stack:
			if lam(q):
				resp_stack.remove(q)
				return (True, q)
		if not GLOBAL_VERIFICATION_LOCK:
			break
	return False, None

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
				is_active = resp[2][13]
				if is_active == 'ACTIVE':
					return OrderConfirmationParser(resp)
				else:
					raise Exception('New order non active status!')
			elif 'oc' in resp:
				is_active = resp[2][13]
				if is_active == 'CANCELED':
					return OrderConfirmationParser(resp)
				else:
					return OrderStreamUpdateParser(resp)
			elif 'ou' in resp:
				is_active = resp[2][13]
				if is_active == 'ACTIVE':
					return OrderConfirmationParser(resp)
				else:
					return OrderStreamUpdateParser(resp)
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
		self.order_update_lock = False
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
		self.order_stream_update_stack = []
		self.active_orders = {}
		self.keep_running = True
		self.is_stopped = False

	def get_order_representation(self, order_id):
		return self.active_orders[order_id]

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
	
	def find_order_by_cid(self, cid):
		for order_id in self.active_orders.keys():
			if self.active_orders[order_id].order_cid == cid:
				return self.active_orders[order_id]
		return None

	def verify_lambda_response(self, lamb):
		request_success, _ = verify_response(self.order_request_stack, lamb)
		confirmation_success, order_confirmation = verify_response(self.order_confirmation_stack, lamb)
		return (request_success and confirmation_success, order_confirmation)

	def verify_order_response(self):
		order_cid_lambda = lambda q: q.order_cid == self.cid_generator.current_cid
		return self.verify_lambda_response(order_cid_lambda)

	def verify_update_order_response(self, order_id):
		order_id_lambda = lambda q: q.order_id == order_id
		return self.verify_lambda_response(order_id_lambda)

	def place_new_order(self, symbol, amount, price):
		new_order_query = self.prepare_new_order_req(self.cid_generator.get_next_cid(), symbol, amount, price)
		self.websocket_connection.send(new_order_query)
		request_confirmation_success, order_confirmation = self.verify_order_response()
		if request_confirmation_success:
			self.approved_order_confirmation_stack[order_confirmation.order_id] = order_confirmation
			if not order_confirmation.order_id in self.active_orders.keys():
				self.active_orders[order_confirmation.order_id] = OrderRepresentation(order_confirmation)
			return request_confirmation_success, order_confirmation.order_id
		else:
			global GLOBAL_VERIFICATION_LOCK
			GLOBAL_VERIFICATION_LOCK = True
			logging.debug('GVL True.')
			order_representation = self.find_order_by_cid(self.cid_generator.current_cid)
			if order_representation:
				return True, order_representation.order_id
			return False, None

	def update_order(self, ord_id, amount, price):
		update_order_query = [0, 'ou', None, {'id': ord_id, 'amount': str(amount), 'price': str(price)}]
		self.websocket_connection.send(json.dumps(update_order_query))
		self.order_update_lock = True
		logging.debug('Update order verify response start.')
		request_confirmation_success, order_confirmation = self.verify_update_order_response(ord_id)
		logging.debug('Update order verify response end.')
		self.order_update_lock = False
		if request_confirmation_success:
			self.approved_order_confirmation_stack[order_confirmation.order_id] = order_confirmation
			self.active_orders[order_confirmation.order_id].update_order_confirmation(order_confirmation)
			return request_confirmation_success
		else:
			global GLOBAL_VERIFICATION_LOCK
			GLOBAL_VERIFICATION_LOCK = True
			logging.debug('GVL True.')
			try:
				if self.active_orders[ord_id].is_active[-1] == 'ACTIVE':
					return False
				elif self.active_orders[ord_id].is_active[-1]['order_status_status'] in ['EXECUTED', 'PARTIALLYFILLED']:
					return True
				else:
					import pdb; pdb.set_trace()
					print('duck')
			except Exception as e:
				print(e)
				import pdb; pdb.set_trace()
				return False

	def cancle_order(self, ord_id):
		cancle_order_query = [0, "oc", None, {"id":ord_id}]
		self.websocket_connection.send(json.dumps(cancle_order_query))
		request_confirmation_success, order_confirmation = self.verify_update_order_response(ord_id)
		self.approved_order_confirmation_stack.pop(order_confirmation.order_id)
		return request_confirmation_success

	def process_order_update(self, resp_factory_object):
		global GLOBAL_VERIFICATION_LOCK
		if type(resp_factory_object) is TradeUpdateParser:
			if resp_factory_object.order_id in self.active_orders.keys():
				self.active_orders[resp_factory_object.order_id].chanle_id = resp_factory_object.chanle_id
				e_p = self.active_orders[resp_factory_object.order_id].exec_price
				e_a = self.active_orders[resp_factory_object.order_id].exec_amount
				self.active_orders[resp_factory_object.order_id].exec_amount += resp_factory_object.exec_amount
				self.active_orders[resp_factory_object.order_id].amount -= resp_factory_object.exec_amount
				self.active_orders[resp_factory_object.order_id].exec_price = (e_p * e_a + resp_factory_object.exec_amount * resp_factory_object.exec_price)/(e_a + resp_factory_object.exec_amount)
				self.active_orders[resp_factory_object.order_id].fee += resp_factory_object.fee
				self.active_orders[resp_factory_object.order_id].fee_currnecy = resp_factory_object.fee_currnecy
				self.active_orders[resp_factory_object.order_id].maker += [resp_factory_object.maker]
			else:
				raise Exception('Processed order is not in active orders list.')
		elif type(resp_factory_object) is OrderStreamUpdateParser:
			if resp_factory_object.order_id in self.active_orders.keys():
				self.active_orders[resp_factory_object.order_id].is_active += [resp_factory_object.status_dictionaty]
				if self.order_update_lock:
					GLOBAL_VERIFICATION_LOCK = False
					logging.debug('GVL False.')
			else:
				order_representation = OrderRepresentation(None)
				order_representation.order_id = resp_factory_object.order_id
				order_representation.order_cid = resp_factory_object.order_cid
				order_representation.symbol = resp_factory_object.symbol
				order_representation.amount = resp_factory_object.amount_orig
				order_representation.price = resp_factory_object.price
				order_representation.order_type = resp_factory_object.type
				order_representation.is_active = [resp_factory_object.status_dictionaty]
				order_representation.chanle_id = 0
				order_representation.exec_amount = 0
				order_representation.exec_price = 0
				order_representation.fee = 0
				order_representation.fee_currnecy = ''
				order_representation.maker = []
				self.active_orders[order_representation.order_id] = order_representation
				GLOBAL_VERIFICATION_LOCK = False
				logging.debug('GVL False.')
	
	def close_thread(self):
		self.keep_running = False
		while not self.is_stopped:
			pass
	
	def run(self):
		while self.keep_running:
			resp = self.websocket_connection.recv()
			if not resp == BITFINEX_HEART_BEAT:
				resp_python_object = json.loads(resp)
				resp_factory_object = self.response_object_factory.get_response_object(resp_python_object)
				# if resp_factory_object:
				# 	pprint(vars(resp_factory_object))
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
					self.process_order_update(resp_factory_object)
				elif type(resp_factory_object) is OrderStreamParser:
					self.order_stream_stack.append(resp_factory_object)
				elif type(resp_factory_object) is OrderStreamUpdateParser:
					self.order_stream_update_stack.append(resp_factory_object)
					self.process_order_update(resp_factory_object)
		self.is_stopped = True

def get_authenticated_client():
	bwsc = BitfinexWebSocketClient(BITFINEX_KEY, BITFINEX_SECRET, NONCE_FACTOR, BITFINEX_API_URL)
	bwsc.start()
	if bwsc.authenticate():
		return bwsc
	else:
		raise Exception('Bitfinex Web Socket Client Authenticatoin Error.')
