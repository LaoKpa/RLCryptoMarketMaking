
import numpy as np
import tensorflow as tf
import gym

# This function selects the probability distribution over actions
from baselines.common.distributions import make_pdtype

"""
This object creates the PPO Network architecture
"""
class MarketMakingPolicy(object):
    def __init__(self, sess, config, reuse = False):
        self.config = config
        self.sess = sess
        # Based on the action space, will select what probability distribution type
        # we will use to distribute action in our stochastic policy (in our case DiagGaussianPdType
        # aka Diagonal Gaussian, 3D normal distribution
        self.pdtype = make_pdtype(gym.spaces.Discrete(config.order_scale_size ** config.action_arg_num))

        self.input_ask_book = tf.placeholder(tf.float32,
            [None, self.config.num_of_frames, self.config.num_of_order_book_entries,
            self.config.order_book_entrie_rep_dim], name="input_ask_book")
    
        self.input_bid_book = tf.placeholder(tf.float32,
            [None, self.config.num_of_frames, self.config.num_of_order_book_entries,
            self.config.order_book_entrie_rep_dim], name="input_bid_book")

        self.input_inventory = tf.placeholder(tf.float32, [None, self.config.num_of_frames, self.config.inventory_vector_size,], name="input_inventory")

        self.input_funds = tf.placeholder(tf.float32, [None, self.config.num_of_frames, self.config.funds_vector_size], name="input_funds")

        with tf.variable_scope("model", reuse = reuse):
            lstm_ask = tf.keras.layers.CuDNNLSTM(self.config.ask_lstm_output_layer_size)
            
            lstm_bid = tf.keras.layers.CuDNNLSTM(self.config.bid_lstm_output_layer_size)

            transformed_input_inventory = tf.contrib.layers.fully_connected(self.input_inventory, self.config.inventory_fc_layer_size)

            transformed_input_funds = tf.contrib.layers.fully_connected(self.input_funds, self.config.funds_fc_layer_size)

            transformed_input_ask_book = tf.contrib.layers.fully_connected(self.input_ask_book, self.config.ask_book_fc_layer_size)

            transformed_input_bid_book = tf.contrib.layers.fully_connected(self.input_bid_book, self.config.bid_book_fc_layer_size)

            lstm_output_ask = tf.transpose(tf.stack([lstm_ask(tf.transpose(transformed_input_ask_book,
                [1,0,2,3])[i]) for i in range(self.config.num_of_frames)]), [1,0,2])
            
            lstm_output_bid = tf.transpose(tf.stack([lstm_bid(tf.transpose(transformed_input_bid_book,
                [1,0,2,3])[i]) for i in range(self.config.num_of_frames)]), [1,0,2])
            
            combined_stacked_state = tf.concat([lstm_output_ask, lstm_output_bid,
                transformed_input_inventory, transformed_input_funds], axis=2)

            transformed_combined_stacked_state = tf.contrib.layers.fully_connected(combined_stacked_state, self.config.final_fc_layer_size)

            lstm_stacked_state = tf.keras.layers.CuDNNLSTM(self.config.stacked_lstm_output_layer_size)

            model_output_vec = lstm_stacked_state(transformed_combined_stacked_state)
            
            last_fc_network = tf.contrib.layers.fully_connected(model_output_vec, self.config.final_fc_layer_before_output_size)

            last_fc_network = tf.contrib.layers.fully_connected(last_fc_network, self.config.final_fc_layer_before_output_size)

            # This build a fc connected layer that returns a probability distribution
            # over actions (self.pd) and our pi logits (self.pi).
            self.pd, self.pi = self.pdtype.pdfromlatent(last_fc_network, init_scale=0.01)

            # Calculate the v(s)
            self.vf = tf.contrib.layers.fully_connected(model_output_vec, 1, activation_fn=None)[:, 0]
        # Take an action in the action distribution (remember we are in a situation
        # of stochastic policy so we don't always take the action with the highest probability
        # for instance if we have 2 actions 0.7 and 0.3 we have 30% chance to take the second)
        self.a0 = self.pd.sample()
        # Calculate the neg log of our probability
        self.neglogp0 = self.pd.neglogp(self.a0)

    # Function use to take a step returns action to take and V(s)
    def step(self, input_ask_book, input_bid_book, input_inventory, input_funds):
        # return a0, vf, neglogp0
        return self.sess.run([self.a0, self.vf, self.neglogp0], {self.input_ask_book:input_ask_book, self.input_bid_book:input_bid_book,
            self.input_inventory:input_inventory, self.input_funds:input_funds})

    # Function that calculates only the V(s)
    def value(self, input_ask_book, input_bid_book, input_inventory, input_funds):
        return self.sess.run(self.vf, {self.input_ask_book:input_ask_book, self.input_bid_book:input_bid_book,
            self.input_inventory:input_inventory, self.input_funds:input_funds})

    # Function that output only the action to take
    def select_action(self, input_ask_book, input_bid_book, input_inventory, input_funds):
        return self.sess.run(self.a0, {self.input_ask_book:input_ask_book, self.input_bid_book:input_bid_book,
            self.input_inventory:input_inventory, self.input_funds:input_funds})
