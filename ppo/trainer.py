
import time

import numpy as np

import tensorflow as tf

import model as ml

import runner as rn

import market_making_game as env

from baselines.common import explained_variance
from baselines import logger

def learn(policy, env, config):

    noptepochs = 4
    nminibatches = 8

    lr = lambda _: 2e-4
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

    # Instantiate the runner object
    runner = rn.Runner(env, model, config)

    # Start total timer
    tfirststart = time.time()

    nupdates = config.total_timesteps//batch_size+1

    for update in range(1, nupdates+1):
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

        for _ in range(noptepochs):
            # Randomize the indexes
            np.random.shuffle(indices)

            # 0 to batch_size with batch_train_size step
            for start in range(0, batch_size, batch_train_size):
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
            
            savepath = "./models/" + str(update) + "/model.ckpt"
            model.save(savepath)
            print('Saving to', savepath)

            # Test our agent with 3 trials and mean the score
            # This will be useful to see if our agent is improving
            test_score = testing(model)
            logger.record_tabular("Mean score test level", test_score)

            logger.dump_tabular()
            
    env.close()

def testing(model):
    """
    We'll use this function to calculate the score on test levels for each saved model,
    to generate the video version
    to generate the map version
    """

    test_env = env.SerialGameEnvironment('../configs/btc_market_making_test_config.txt', 'MARKET_MAKING_CONFIG')
 
    # Play
    total_score = 0
    trial = 0
    
    # We make 3 trials
    for trial in range(1):
        obs = test_env.get_initial_state()
        done = False
        score = 0
        i=0
        while done == False or i<86400:
            # Get the action
            action, _, _ = model.step(*obs)
            # Take action in env and look the results
            obs, reward, done = test_env.step(action)
            print(i)
            i=i+1
            score += reward[0]
        total_score += score
        trial += 1

    # Divide the score by the number of trials
    total_test_score = total_score / 3.0
    return total_test_score
