
import tensorflow as tf
import model as ml
import runner as rn
import utils as ul
import market_making_game as env

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

def learn(policy, env, config):
	eval_env = None
	seed=None
	update_fn=None
	init_fn=None
	comm=None
	total_timesteps = config.total_timesteps
	nsteps = config.nsteps
	ent_coef=config.ent_coef
	lr=lambda x: config.lr
	max_grad_norm=config.max_grad_norm
	vf_coef=config.vf_coef
	gamma=config.gamma
	lam=config.lam
	log_interval=config.log_interval
	nminibatches=config.nminibatches
	noptepochs=config.noptepochs
	cliprange=lambda x: config.cliprange
	save_interval=config.save_interval

	set_global_seeds(seed)

	if isinstance(lr, float): lr = constfn(lr)
	else: assert callable(lr)
	if isinstance(cliprange, float): cliprange = constfn(cliprange)
	else: assert callable(cliprange)
	total_timesteps = int(total_timesteps)

	# Get the nb of env
	nenvs = env.num_envs

	# Calculate the batch_size
	nbatch = nenvs * nsteps
	nbatch_train = nbatch // nminibatches
	is_mpi_root = (MPI is None or MPI.COMM_WORLD.Get_rank() == 0)

	# Instantiate the model object (that creates act_model and train_model)
	model = ml.Model(policy, config)

	load_path = ul.get_current_saved_model_path(config.load_model_path)
	if not load_path == '':
		model.load(load_path)

	# Instantiate the runner object
	runner = rn.Runner(env, model, config)
	if eval_env is not None:
		eval_runner = rn.Runner(eval_env, model, config)

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
		# obs, returns, masks, actions, values, neglogpacs, states, epinfos = runner.run() #pylint: disable=E0632
		obs, returns, actions, values, neglogpacs = runner.run()

		if eval_env is not None:
			eval_obs, eval_returns, eval_masks, eval_actions, eval_values, eval_neglogpacs, eval_states, eval_epinfos = eval_runner.run() #pylint: disable=E0632

		if update % log_interval == 0 and is_mpi_root: logger.info('Done.')

		# Here what we're going to do is for each minibatch calculate the loss and append it.
		mblossvals = []

		# Index of each element of batch_size
		# Create the indices array
		inds = np.arange(nbatch)
		for _ in range(noptepochs):
			# Randomize the indexes
			np.random.shuffle(inds)
			# 0 to batch_size with batch_train_size step
			for start in range(0, nbatch, nbatch_train):
				print('Trainer Progress Count: {0}/{1}'.format(start, nbatch_train), end='\r', flush=True)
				end = start + nbatch_train
				mbinds = inds[start:end]
				slices = (arr[mbinds] for arr in (obs, returns, actions, values, neglogpacs))
				mblossvals.append(model.train(lrnow, cliprangenow, *slices))

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
			if update % 10 == 0:
				testing(model)
			ev = explained_variance(values, returns)
			logger.logkv("misc/serial_timesteps", update*nsteps)
			logger.logkv("misc/nupdates", update)
			logger.logkv("misc/total_timesteps", update*nbatch)
			logger.logkv("fps", fps)
			logger.logkv("misc/explained_variance", float(ev))
			logger.logkv('misc/time_elapsed', tnow - tfirststart)
			for (lossval, lossname) in zip(lossvals, model.loss_names):
				logger.logkv('loss/' + lossname, lossval)

			logger.dumpkvs()
		if  update % save_interval == 0:
			checkdir = osp.join(config.save_model_path, 'checkpoints')
			os.makedirs(checkdir, exist_ok=True)
			savepath = osp.join(checkdir, '%.5i'%update)
			print('Saving to', savepath)
			model.save(savepath)
	return model

# Avoid division error when calculate the mean (in our case if epinfo is empty returns np.nan, not return an error)
def safemean(xs):
	return np.nan if len(xs) == 0 else np.mean(xs)

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
			action, _, _ = model.step(obs)
			obs, reward, done, t = test_env.step(action)
			i=i+1
			score += reward[0]
			inv = test_env.envs[0].game.order_book.state_space.inventory
			price = test_env.envs[0].game.order_book.get_current_price()
			funds = test_env.envs[0].game.order_book.state_space.available_funds
			net_worth = funds + inv * price
			print ('nw: {0} | count: {1}'.format(net_worth, i))
		total_score += score
		trial += 1
	# Divide the score by the number of trials
	total_test_score = total_score / 1.0
	return total_test_score
