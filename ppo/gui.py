
import sys
import imp
import time

import pickle as pk
import market_making_game as env
import PyQt4.QtGui as qg

import config_helper as ch
import utils as ul
import time

import numpy as np

import tensorflow as tf
import policy
import model as ml

import runner as rn

import market_making_game as env

from baselines.common import explained_variance
from baselines import logger

import gym
import math
import os

import trainer

CH = imp.load_source('config_helper', '../generic/config_helper.py')

class MarketMakingGui(object):
	def __init__(self, config):
		self.model = ml.Model(policy.MarketMakingPolicy, config)
		load_path = ul.get_current_saved_model_path(config.save_model_path)
		self.model.load(load_path)
		self.ob_fh = open('/home/lavi/Downloads/ob.bin', 'rb')
		self.app = qg.QApplication(sys.argv)
		self.create_window()
		self.create_button()
		self.create_labels()
		self.create_simu_table()
		self.create_display_table()
		self.create_layout()
		self.window.show()
		self.app.exec_()
		sys.exit()

	def create_window(self):
		self.window = qg.QWidget()
		self.window.setWindowTitle("Market Making Simulation")
		self.window.resizeEvent = self.windowResizeCallback
	
	def create_button(self):
		self.btn = qg.QPushButton(self.window)
		self.btn.setObjectName("pb")
		self.btn.clicked.connect(self.callback)
		self.btn.setText("load book")

	def create_labels(self):
		self.main_label = qg.QLabel("Market Making Visualisation")
		font = qg.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.main_label.setFont(font)

	def create_simu_table(self):
		self.table = qg.QTableWidget()
		self.table.setRowCount(25)
		self.table.setColumnCount(4)
		self.table.setHorizontalHeaderLabels\
		(['ask_amount', 'ask_price', 'bid_price', 'bit_amount'])

	def create_display_table(self):
		self.display_table = qg.QTableWidget()
		self.display_table.setRowCount(1)
		self.display_table.setColumnCount(4)
		self.display_table.setHorizontalHeaderLabels\
		(['inventory', 'funds', 'net_worth', 'price'])

	def create_layout(self):
		self.layout = qg.QFormLayout(self.window)
		self.layout.addWidget(self.main_label)
		self.layout.addWidget(self.table)
		self.layout.addWidget(self.display_table)
		self.layout.addWidget(self.btn)

	def organize_widgets(self):
		self.main_label.move(300, 10)
		self.table.move(200, 125)
		self.table.resize(450, 800)
		self.display_table.move(200, 50)
		self.display_table.resize(450, 55)
		self.btn.move(10, 110)
		self.btn.resize(100, 40)

	def windowResizeCallback(self, obj):
		self.organize_widgets()

	def print_order_book(self, ob):
		for ask, i in zip(ob['asks'], range(len(ob['asks']))):
			if ask['my_order']:
				color='yellow'
			else:
				color='green'
			price_item = qg.QTableWidgetItem()
			price_item.setBackgroundColor(qg.QColor(color))
			price_item.setText(str(ask['price']))
			amount_item = qg.QTableWidgetItem()
			amount_item.setBackgroundColor(qg.QColor(color))
			amount_item.setText(str(ask['amount']))
			self.table.setItem(i,0, amount_item)
			self.table.setItem(i,1, price_item)
		for bid, i in zip(ob['bids'], range(len(ob['bids']))):
			if bid['my_order']:
				color='yellow'
			else:
				color='red'
			price_item = qg.QTableWidgetItem()
			price_item.setBackgroundColor(qg.QColor(color))
			price_item.setText(str(bid['price']))
			amount_item = qg.QTableWidgetItem()
			amount_item.setBackgroundColor(qg.QColor(color))
			amount_item.setText(str(bid['amount']))
			self.table.setItem(i,2, price_item)
			self.table.setItem(i,3, amount_item)
	
	def print_stats(self, inv, price, funds, net_worth):
		inv_item = qg.QTableWidgetItem()
		# inv_item.setBackgroundColor(qg.QColor(color))
		inv_item.setText(str(inv))

		price_item = qg.QTableWidgetItem()
		# price_item.setBackgroundColor(qg.QColor(color))
		price_item.setText(str(price))

		funds_item = qg.QTableWidgetItem()
		# price_item.setBackgroundColor(qg.QColor(color))
		funds_item.setText(str(funds))

		net_worth_item = qg.QTableWidgetItem()
		# price_item.setBackgroundColor(qg.QColor(color))
		net_worth_item.setText(str(net_worth))

		self.display_table.setItem(0,0, inv_item)
		self.display_table.setItem(0,1, funds_item)
		self.display_table.setItem(0,2, net_worth_item)
		self.display_table.setItem(0,3, price_item)

	def callback(self):
		test_env = env.SerialGameEnvironment\
			('../configs/btc_market_making_test_config.txt', 'MARKET_MAKING_CONFIG')
		total_score = 0
		trial = 0
		for trial in range(1):
			obs = test_env.get_initial_state()
			done = False
			score = 0
			inv = 0
			net_worth = 0
			funds = 0
			i=0
			while done == False and i<86400:
				self.print_order_book(test_env.envs[0].game.order_book.current_order_book)
				action, _, _ = self.model.step(*obs)
				obs, reward, done = test_env.step(action)
				i=i+1
				score += reward[0]
				inv = test_env.envs[0].game.order_book.state_space.inventory
				price = test_env.envs[0].game.order_book.state_space.current_price
				funds = test_env.envs[0].game.order_book.state_space.available_funds
				net_worth = funds + inv * price
				self.print_stats(inv, price, funds, net_worth)
				# print (net_worth)
				#time.sleep(0.1)
				qg.qApp.processEvents()
			total_score += score
			trial += 1
		total_test_score = total_score / 1.0
		return total_test_score

def main():
	config = tf.ConfigProto()
	# Avoid warning message errors
	os.environ["CUDA_VISIBLE_DEVICES"]="0"
	# Allowing GPU memory growth
	config.gpu_options.allow_growth = True
	bootstrap_config = ch.ConfigHelper\
		('../configs/btc_market_making_config.txt', 'MARKET_MAKING_CONFIG')
	with tf.Session(config=config):
		mmg = MarketMakingGui(bootstrap_config)

if __name__ == '__main__':
		main()
