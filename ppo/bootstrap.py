

import tensorflow as tf
import numpy as np
import gym
import math
import os

import model
import trainer
import policy
import market_making_game as env

def main():
    config = tf.ConfigProto()

    # Avoid warning message errors
    os.environ["CUDA_VISIBLE_DEVICES"]="0"

    # Allowing GPU memory growth
    config.gpu_options.allow_growth = True

    with tf.Session(config=config):
        trainer.learn(policy=policy.MarketMakingPolicy,
                            env=env.SerialGameEnvironment('../configs/btc_market_making_config.txt', 'MARKET_MAKING_CONFIG', 5, 4),
                            nsteps=2048, # Steps per environment
                            total_timesteps=10000000,
                            gamma=0.99,
                            lam = 0.95,
                            vf_coef=0.5,
                            ent_coef=0.01,
                            lr = lambda _: 2e-4,
                            cliprange = lambda _: 0.1, # 0.1 * learning_rate
                            max_grad_norm = 0.5, 
                            log_interval = 10
                            )

if __name__ == '__main__':
    main()
