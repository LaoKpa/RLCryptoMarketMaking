
import tensorflow as tf
import numpy as np
import gym
import math
import os

import model
import trainer
import policy
import market_making_game as env
import config_helper as ch

def main():
    config = tf.ConfigProto()

    # Avoid warning message errors
    os.environ["CUDA_VISIBLE_DEVICES"]="0"

    # Allowing GPU memory growth
    config.gpu_options.allow_growth = True

    bootstrap_config = ch.ConfigHelper('../configs/btc_market_making_config.txt', 'MARKET_MAKING_CONFIG')

    with tf.Session(config=config):
        trainer.learn(policy.MarketMakingPolicy,
        env.SerialGameEnvironment('../configs/btc_market_making_config.txt', 'MARKET_MAKING_CONFIG'), bootstrap_config)

if __name__ == '__main__':
    main()
