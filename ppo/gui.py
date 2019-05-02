
import sys
import imp
import time

import pickle as pk
import market_making_game as env
import PyQt4.QtGui as qg

import config_helper as ch

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
		load_path = "/home/lavi/Documents/RLMM/models/190/model.ckpt"
		self.model.load(load_path)
		self.ob_fh = open('/home/lavi/Downloads/ob.bin', 'rb')
		self.app = qg.QApplication(sys.argv)
		self.create_window()
		self.create_button()
		self.create_labels()
		self.init_table()
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
		self.inv_label = qg.QLabel("Inventory:")
		self.funds_label = qg.QLabel("Funds:")
		self.worth_label = qg.QLabel("Worth:")


	def init_table(self):
		self.table = qg.QTableWidget()
		self.table.setRowCount(25)
		self.table.setColumnCount(4)
		self.table.setHorizontalHeaderLabels\
		(['ask_amount', 'ask_price', 'bid_price', 'bit_amount'])

	def create_layout(self):
		self.layout = qg.QFormLayout(self.window)
		self.layout.addWidget(self.main_label)
		self.layout.addWidget(self.inv_label)
		self.layout.addWidget(self.worth_label)
		self.layout.addWidget(self.funds_label)
		self.layout.addWidget(self.table)
		self.layout.addWidget(self.btn)

	def organize_widgets(self):
		self.main_label.move(300, 10)
		self.inv_label.move(10, 50)
		self.worth_label.move(10, 70)
		self.funds_label.move(10, 90)
		self.table.move(200, 50)
		self.table.resize(450, 800)
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
				self.inv_label.setText('Inventory: {0}'.format(inv))
				self.organize_widgets()
				self.funds_label.setText('Funds: {0}'.format(funds))
				self.organize_widgets()
				self.worth_label.setText('Worth: {0}'.format(net_worth))
				self.organize_widgets()
				self.print_order_book(test_env.envs[0].game.order_book.current_order_book)
				action, _, _ = self.model.step(*obs)
				obs, reward, done = test_env.step(action)
				i=i+1
				score += reward[0]
				inv = test_env.envs[0].game.order_book.state_space.inventory
				price = test_env.envs[0].game.order_book.state_space.current_price
				funds = test_env.envs[0].game.order_book.state_space.available_funds
				net_worth = funds + inv * price
				#print (net_worth)
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
