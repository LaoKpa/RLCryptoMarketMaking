
import time

import numpy as np

import tensorflow as tf

import model as ml

import runner as rn
import utils as ul
import market_making_game as env

from baselines.common import explained_variance
from baselines import logger

def learn(policy, env, config):
	noptepochs = 8
	nminibatches = 8

	lr = lambda _: 0.0001
	cliprange = lambda _: 0.1

	if isinstance(lr, float): lr = constfn(lr)
	else: assert callable(lr)
	if isinstance(cliprange, float): cliprange = constfn(cliprange)
	else: assert callable(cliprange)

	# Get the nb of env
	nenvs = env.num_envs

	# Calculate the batch_size
	batch_size = config.num_of_envs * config.nsteps # For instance if we take 5 steps and we have 5 environments batch_size = 25

	batch_train_size = batch_size // nminibatches

	assert batch_size % nminibatches == 0
	# Instantiate the model object (that creates step_model and train_model)
	model = ml.Model(policy, config)

	# Load the model
	# If you want to continue training
	# load_path = "./models/40/model.ckpt"
	# model.load(load_path)

	load_path = ul.get_current_saved_model_path(config.save_model_path)
	if not load_path == '':
		model.load(load_path)
	# Instantiate the runner object
	runner = rn.Runner(env, model, config)

	# Start total timer
	tfirststart = time.time()

	nupdates = config.total_timesteps // batch_size+1

	for update in range(1, nupdates+1):
		print('{0}/{1}'.format(update, nupdates))
		# Start timer
		tstart = time.time()

		frac = 1.0 - (update - 1.0) / nupdates

		# Calculate the learning rate
		lrnow = lr(frac)

		# Calculate the cliprange
		cliprangenow = cliprange(frac)

		# Get minibatch
		ask_book_env, bid_book_env, inv_env, funds_env, returns, actions, values, neglogpacs = runner.run()
				
		# Here what we're going to do is for each minibatch calculate the loss and append it.
		mb_losses = []
		total_batches_train = 0

		# Index of each element of batch_size
		# Create the indices array
		indices = np.arange(batch_size)
		print('\n')
		for _ in range(noptepochs):
			# Randomize the indexes
			np.random.shuffle(indices)
			# 0 to batch_size with batch_train_size step
			for start in range(0, batch_size, batch_train_size):
				print('Trainer Progress Count: {0}/{1}'.format(start, batch_size), end='\r', flush=True)
				end = start + batch_train_size
				mbinds = indices[start:end]
				slices = (arr[mbinds] for arr in (ask_book_env, bid_book_env, inv_env, funds_env, actions, returns, values, neglogpacs))
				mb_losses.append(model.train(*slices, lrnow, cliprangenow))
	
		# Feedforward --> get losses --> update
		lossvalues = np.mean(mb_losses, axis=0)

		# End timer
		tnow = time.time()

		# Calculate the fps (frame per second)
		fps = int(batch_size / (tnow - tstart))

		if update % config.log_interval == 0 or update == 1:
			"""
			Computes fraction of variance that ypred explains about y.
			Returns 1 - Var[y-ypred] / Var[y]
			interpretation:
			ev=0  =>  might as well have predicted zero
			ev=1  =>  perfect prediction
			ev<0  =>  worse than just predicting zero
			"""
			ev = explained_variance(values, returns)
			logger.record_tabular("serial_timesteps", update * config.nsteps)
			logger.record_tabular("nupdates", update)
			logger.record_tabular("total_timesteps", update*batch_size)
			logger.record_tabular("fps", fps)
			logger.record_tabular("policy_loss", float(lossvalues[0]))
			logger.record_tabular("policy_entropy", float(lossvalues[2]))
			logger.record_tabular("value_loss", float(lossvalues[1]))
			logger.record_tabular("explained_variance", float(ev))
			logger.record_tabular("time elapsed", float(tnow - tfirststart))
			
			savepath = config.save_model_path + '/' + str(update) + '/model.ckpt'
			model.save(savepath)
			print('Saving to', savepath)

			# Test our agent with 3 trials and mean the score
			# This will be useful to see if our agent is improving
			if update % 10 == 0:
				test_score = testing(model)
				logger.record_tabular("Mean score test level", test_score)

			logger.dump_tabular()
			
	env.close()

def testing(model):
	test_env = env.ParallelGameEnvironment('../configs/btc_market_making_test_config.txt', 'MARKET_MAKING_CONFIG')
	# Play
	total_score = 0
	trial = 0
	# We make 3 trials
	for trial in range(1):
		obs = test_env.get_initial_state()
		done = False
		score = 0
		i=0
		while done == False and i < 10000:
			action, _, _ = model.step(*obs)
			obs, reward, done, t = test_env.step(action)
			i=i+1
			score += reward[0]
			inv = test_env.envs[0].game.order_book.state_space.inventory
			price = test_env.envs[0].game.order_book.state_space.current_price
			funds = test_env.envs[0].game.order_book.state_space.available_funds
			net_worth = funds + inv * price
			print ('nw: {0} | count: {1}'.format(net_worth, i))
		total_score += score
		trial += 1
	# Divide the score by the number of trials
	total_test_score = total_score / 1.0
	return total_test_score



import os
import time
import numpy as np
import os.path as osp
from baselines import logger
from collections import deque
from baselines.common import explained_variance, set_global_seeds
from baselines.common.policies import build_policy
try:
	from mpi4py import MPI
except ImportError:
	MPI = None
from baselines.ppo2.runner import Runner


def constfn(val):
	def f(_):
		return val
	return f

def learn(policy, model_fn, env, config, eval_env = None, seed=None,\
	update_fn=None, init_fn=None, comm=None):
	total_timesteps = config.total_timesteps
	nsteps = config.nsteps
	ent_coef=config.ent_coef
	lr=config.lr
	max_grad_norm=config.max_grad_norm
	vf_coef=config.vf_coef
	gamma=config.gamma
	lam=config.lam
	log_interval=config.log_interval
	nminibatches=config.nminibatches
	noptepochs=config.noptepochs
	cliprange=config.cliprange
	save_interval=config.save_interval
	mpi_rank_weight=config.mpi_rank_weight
	
	load_path = ul.get_current_saved_model_path(config.save_model_path)
	if not load_path == '':
		model.load(load_path)

	set_global_seeds(seed)

	if isinstance(lr, float): lr = constfn(lr)
	else: assert callable(lr)
	if isinstance(cliprange, float): cliprange = constfn(cliprange)
	else: assert callable(cliprange)
	total_timesteps = int(total_timesteps)

	# Get the nb of env
	nenvs = env.num_envs

	# Get state_space and action_space
	ob_space = env.observation_space
	ac_space = env.action_space

	# Calculate the batch_size
	nbatch = nenvs * nsteps
	nbatch_train = nbatch // nminibatches
	is_mpi_root = (MPI is None or MPI.COMM_WORLD.Get_rank() == 0)

	# Instantiate the model object (that creates act_model and train_model)
	model = model_fn(policy, config)

	if load_path is not None:
		model.load(load_path)
	# Instantiate the runner object
	runner = rn.Runner(env, model, config)
	if eval_env is not None:
		eval_runner = rn.Runner(eval_env, model, config)

	epinfobuf = deque(maxlen=100)
	if eval_env is not None:
		eval_epinfobuf = deque(maxlen=100)

	if init_fn is not None:
		init_fn()

	# Start total timer
	tfirststart = time.perf_counter()

	nupdates = total_timesteps//nbatch
	for update in range(1, nupdates+1):
		assert nbatch % nminibatches == 0
		# Start timer
		tstart = time.perf_counter()
		frac = 1.0 - (update - 1.0) / nupdates
		# Calculate the learning rate
		lrnow = lr(frac)
		# Calculate the cliprange
		cliprangenow = cliprange(frac)

		if update % log_interval == 0 and is_mpi_root: logger.info('Stepping environment...')

		# Get minibatch
		obs, returns, masks, actions, values, neglogpacs, states, epinfos = runner.run() #pylint: disable=E0632
		ask_book_env, bid_book_env, inv_env, funds_env, returns, actions, values, neglogpacs = runner.run()

		if eval_env is not None:
			eval_obs, eval_returns, eval_masks, eval_actions, eval_values, eval_neglogpacs, eval_states, eval_epinfos = eval_runner.run() #pylint: disable=E0632

		if update % log_interval == 0 and is_mpi_root: logger.info('Done.')

		epinfobuf.extend(epinfos)
		if eval_env is not None:
			eval_epinfobuf.extend(eval_epinfos)

		# Here what we're going to do is for each minibatch calculate the loss and append it.
		mblossvals = []
		if states is None: # nonrecurrent version
			# Index of each element of batch_size
			# Create the indices array
			inds = np.arange(nbatch)
			for _ in range(noptepochs):
				# Randomize the indexes
				np.random.shuffle(inds)
				# 0 to batch_size with batch_train_size step
				for start in range(0, nbatch, nbatch_train):
					end = start + nbatch_train
					mbinds = inds[start:end]
					slices = (arr[mbinds] for arr in (obs, returns, masks, actions, values, neglogpacs))
					mblossvals.append(model.train(lrnow, cliprangenow, *slices))

				for start in range(0, batch_size, batch_train_size):
					print('Trainer Progress Count: {0}/{1}'.format(start, batch_size), end='\r', flush=True)
					end = start + batch_train_size
					mbinds = indices[start:end]
					slices = (arr[mbinds] for arr in (ask_book_env, bid_book_env, inv_env, funds_env, actions, returns, values, neglogpacs))
					mb_losses.append(model.train(*slices, lrnow, cliprangenow))

		else: # recurrent version
			assert nenvs % nminibatches == 0
			envsperbatch = nenvs // nminibatches
			envinds = np.arange(nenvs)
			flatinds = np.arange(nenvs * nsteps).reshape(nenvs, nsteps)
			for _ in range(noptepochs):
				np.random.shuffle(envinds)
				for start in range(0, nenvs, envsperbatch):
					end = start + envsperbatch
					mbenvinds = envinds[start:end]
					mbflatinds = flatinds[mbenvinds].ravel()
					slices = (arr[mbflatinds] for arr in (obs, returns, masks, actions, values, neglogpacs))
					mbstates = states[mbenvinds]
					mblossvals.append(model.train(lrnow, cliprangenow, *slices, mbstates))

		# Feedforward --> get losses --> update
		lossvals = np.mean(mblossvals, axis=0)
		# End timer
		tnow = time.perf_counter()
		# Calculate the fps (frame per second)
		fps = int(nbatch / (tnow - tstart))

		if update_fn is not None:
			update_fn(update)

		if update % log_interval == 0 or update == 1:
			# Calculates if value function is a good predicator of the returns (ev > 1)
			# or if it's just worse than predicting nothing (ev =< 0)
			ev = explained_variance(values, returns)
			logger.logkv("misc/serial_timesteps", update*nsteps)
			logger.logkv("misc/nupdates", update)
			logger.logkv("misc/total_timesteps", update*nbatch)
			logger.logkv("fps", fps)
			logger.logkv("misc/explained_variance", float(ev))
			logger.logkv('eprewmean', safemean([epinfo['r'] for epinfo in epinfobuf]))
			logger.logkv('eplenmean', safemean([epinfo['l'] for epinfo in epinfobuf]))
			if eval_env is not None:
				logger.logkv('eval_eprewmean', safemean([epinfo['r'] for epinfo in eval_epinfobuf]) )
				logger.logkv('eval_eplenmean', safemean([epinfo['l'] for epinfo in eval_epinfobuf]) )
			logger.logkv('misc/time_elapsed', tnow - tfirststart)
			for (lossval, lossname) in zip(lossvals, model.loss_names):
				logger.logkv('loss/' + lossname, lossval)

			logger.dumpkvs()
		if save_interval and (update % save_interval == 0 or update == 1) and logger.get_dir() and is_mpi_root:
			checkdir = osp.join(logger.get_dir(), 'checkpoints')
			os.makedirs(checkdir, exist_ok=True)
			savepath = osp.join(checkdir, '%.5i'%update)
			print('Saving to', savepath)
			model.save(savepath)

	return model
# Avoid division error when calculate the mean (in our case if epinfo is empty returns np.nan, not return an error)
def safemean(xs):
	return np.nan if len(xs) == 0 else np.mean(xs)