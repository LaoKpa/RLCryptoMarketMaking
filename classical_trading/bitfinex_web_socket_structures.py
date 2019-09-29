
def print_stack_stats(bitfinex_web_socket_client):
	print('order_confirmation_stack length: {0}'.format(len(bitfinex_web_socket_client.order_confirmation_stack)))
	print('order_request_stack length: {0}'.format(len(bitfinex_web_socket_client.order_request_stack)))
	print('authentication_stack length: {0}'.format(len(bitfinex_web_socket_client.authentication_stack)))
	print('approved_order_confirmation_stack length: {0}'.format(len(bitfinex_web_socket_client.approved_order_confirmation_stack)))
	print('trade_event_stack length: {0}'.format(len(bitfinex_web_socket_client.trade_event_stack)))
	print('trade_update_stack length: {0}'.format(len(bitfinex_web_socket_client.trade_update_stack)))
	print('order_stream_stack length: {0}'.format(len(bitfinex_web_socket_client.order_stream_stack)))

def parse_update_status(order_status_string):
	def parse_splitted_order_status(order_status):
		splitted_order_status = order_status.replace(' ', '').split('@')
		executed_amount = float(splitted_order_status[1].split('(')[1].split(')')[0])
		executed_price = float(splitted_order_status[1].split('(')[0])
		order_status_status = splitted_order_status[0]
		return executed_amount, executed_price, order_status_status
	try:
		if '(note:POSCLOSE)' in order_status_string:
			if len([ i for i in order_status_string if i == ':']) == 1:
				splitted_order_status, _ = order_status_string.replace(' ', '').split(':')
			else:
				splitted_order_status, _, _ = order_status_string.replace(' ', '').split(':')
			executed_amount, executed_price, order_status_status = parse_splitted_order_status(splitted_order_status)
			return {'executed_amount':executed_amount, 'executed_price':executed_price, 'order_status_status':order_status_status}
		if 'EXECUTED' in order_status_string and 'PARTIALLY' in order_status_string and 'was' in order_status_string:
			if len([ i for i in order_status_string if i == ':']) == 1:
				splitted_order_status, _ = order_status_string.replace(' ', '').split(':')
			else:
				import pdb; pdb.set_trace()
				splitted_order_status, _, _ = order_status_string.replace(' ', '').split(':')
			executed_amount, executed_price, order_status_status = parse_splitted_order_status(splitted_order_status)
			return {'executed_amount':executed_amount, 'executed_price':executed_price, 'order_status_status':order_status_status}
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
	except Exception as e:
		import pdb; pdb.set_trace()
		print(e)

class OrderRepresentation(object):
	def __init__(self, order_confirmation=None):
		if order_confirmation:
			self.order_id = order_confirmation.order_id
			self.order_cid = order_confirmation.order_cid
			self.symbol = order_confirmation.symbol
			self.amount = order_confirmation.amount
			self.price = order_confirmation.price
			self.order_type = order_confirmation.type
			self.is_active = [order_confirmation.is_active]
			self.chanle_id = 0
			self.exec_amount = 0
			self.exec_price = 0
			self.fee = 0
			self.fee_currnecy = ''
			self.maker = []

	def update_order_confirmation(self, order_confirmation):
		self.symbol = order_confirmation.symbol
		self.amount = order_confirmation.amount
		self.price = order_confirmation.price
		self.order_type = order_confirmation.type

class OrderStreamUpdateParser(object):
	def __init__(self, order_request_responsoe):
		self.chanle_id = order_request_responsoe[0]
		self.event_string = order_request_responsoe[1]
		if order_request_responsoe[2] == []:
			return
		self.order_id = order_request_responsoe[2][0]
		self.order_gid = order_request_responsoe[2][1]
		self.order_cid = order_request_responsoe[2][2]
		self.symbol = order_request_responsoe[2][3]
		self.mts_create = order_request_responsoe[2][4]
		self.mts_update = order_request_responsoe[2][5]
		self.amount = order_request_responsoe[2][6]
		self.amount_orig = order_request_responsoe[2][7]
		self.type = order_request_responsoe[2][8]
		self.type_prev = order_request_responsoe[2][9]
		self.flags = order_request_responsoe[2][12]
		self.status = order_request_responsoe[2][13]
		self.status_dictionaty = parse_update_status(self.status)
		self.price = order_request_responsoe[2][16]
		self.price_avg = order_request_responsoe[2][17]
		self.price_trailing = order_request_responsoe[2][18]
		self.price_aux_limit = order_request_responsoe[2][19]
		self.notify = order_request_responsoe[2][23]
		self.hidden = order_request_responsoe[2][24]
		self.placed_id = order_request_responsoe[2][25]
		self.routing = order_request_responsoe[2][28]

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
		self.status_dictionaty = parse_update_status(self.status)
		self.price = order_request_responsoe[2][0][16]
		self.price_avg = order_request_responsoe[2][0][17]
		self.price_aux_limit = order_request_responsoe[2][0][18]
		self.notify = order_request_responsoe[2][0][22]
		self.hidden = order_request_responsoe[2][0][23]
		self.placed_id = order_request_responsoe[2][0][24]
		self.routing = order_request_responsoe[2][0][27]

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
		try:
			self.request_string = order_request_responsoe[2][1]
			if order_request_responsoe[2][4]:
				self.order_id = order_request_responsoe[2][4][0]
				self.order_cid = order_request_responsoe[2][4][2]
				self.symbol = order_request_responsoe[2][4][3]
				self.amount = order_request_responsoe[2][4][6]
				self.type = order_request_responsoe[2][4][8]
				self.is_active = order_request_responsoe[2][4][13]
				self.price = order_request_responsoe[2][4][16]
			else:
				self.order_id = 0
				self.order_cid = 0
			self.is_successful = order_request_responsoe[2][6]
			self.message = order_request_responsoe[2][7]
		except Exception as e:
			import pdb; pdb.set_trace()
			print('OrderRequestParser')

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
