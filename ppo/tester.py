
import sys
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
import utils as ul
import trainer

class MarketMakingCLITester(object):
	def __init__(self, config):
		self.model = ml.Model(policy.MarketMakingPolicy, config)
		load_path = ul.get_current_saved_model_path(config.save_model_path)
		self.model.load(load_path)
		self.test_model()

	def test_model(self):
		test_env = env.ParallelGameEnvironment\
			('../configs/btc_market_making_test_config.txt', 'MARKET_MAKING_CONFIG')
		total_score = 0
		trial = 0
		tmp_inv = 0
		for trial in range(1):
			obs = test_env.get_initial_state()
			done = False
			score = 0
			i=0
			while done == False:
				action, _, _ = self.model.step(*obs)
				obs, reward, done, t = test_env.step(action)
				i=i+1
				score += reward[0]
				inv = test_env.envs[0].game.order_book.state_space.inventory
				if abs(inv-tmp_inv) > 100:
					import pdb; pdb.set_trace()
				tmp_inv = inv
				price = test_env.envs[0].game.order_book.state_space.current_price
				funds = test_env.envs[0].game.order_book.state_space.available_funds
				net_worth = funds + inv * price
				print('nw: {0} | inv: {1}| price: {2}| funds: {3}| count: {4}'.format(net_worth, inv, price, funds, i))
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
		mmg = MarketMakingCLITester(bootstrap_config)

if __name__ == '__main__':
	main()
