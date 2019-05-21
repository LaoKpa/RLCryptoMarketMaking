
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

        self.input_states = tf.placeholder(tf.float32,\
            [None, self.config.num_of_frames, self.config.num_of_representation_vectors, self.config.representation_vector_size], name="input_states")

        with tf.variable_scope("model", reuse = reuse):
            
            reshaped_input_states = tf.reshape(self.input_states, (tf.shape(self.input_states)[0],\
                self.config.num_of_frames, self.config.num_of_representation_vectors * self.config.representation_vector_size))

            reshaped_input_states_fc_1 = tf.contrib.layers.fully_connected(reshaped_input_states, self.config.states_fc_layer_1_size)

            reshaped_input_states_fc_2 = tf.contrib.layers.fully_connected(reshaped_input_states_fc_1, self.config.states_fc_layer_2_size)

            reshaped_input_states_fc_3 = tf.contrib.layers.fully_connected(reshaped_input_states_fc_2, self.config.states_fc_layer_3_size)

            last_fc_layer_before_lstm = tf.contrib.layers.fully_connected(reshaped_input_states_fc_3, self.config.states_fc_layer_4_size)

            lstm_stacked_state = tf.keras.layers.CuDNNLSTM(self.config.stacked_lstm_output_layer_size)

            model_output_vec = lstm_stacked_state(last_fc_layer_before_lstm)
            
            post_lstm_fc_layer_1 = tf.contrib.layers.fully_connected(model_output_vec, self.config.post_lstm_fc_layer_1_size)

            post_lstm_fc_layer_2 = tf.contrib.layers.fully_connected(post_lstm_fc_layer_1, self.config.post_lstm_fc_layer_2_size)

            last_fc_network = tf.contrib.layers.fully_connected(post_lstm_fc_layer_2, self.config.post_lstm_fc_layer_3_size)

            # This build a fc connected layer that returns a probability distribution
            # over actions (self.pd) and our pi logits (self.pi).
            self.pd, self.pi = self.pdtype.pdfromlatent(last_fc_network, init_scale=0.01)

            # Calculate the v(s)
            vf_fc_layer_1 = tf.contrib.layers.fully_connected(last_fc_network, self.config.vf_fc_layer_1_size)
            vf_fc_layer_2 = tf.contrib.layers.fully_connected(vf_fc_layer_1, self.config.vf_fc_layer_2_size)
            vf_fc_layer_final = tf.contrib.layers.fully_connected(vf_fc_layer_2, self.config.vf_fc_layer_3_size)
            self.vf = tf.contrib.layers.fully_connected(vf_fc_layer_final, 1, activation_fn=None)[:, 0]
        # Take an action in the action distribution (remember we are in a situation
        # of stochastic policy so we don't always take the action with the highest probability
        # for instance if we have 2 actions 0.7 and 0.3 we have 30% chance to take the second)
        self.a0 = self.pd.sample()
        # Calculate the neg log of our probability
        self.neglogp0 = self.pd.neglogp(self.a0)

    # Function use to take a step returns action to take and V(s)
    def step(self, input_states):
        # return a0, vf, neglogp0
        return self.sess.run([self.a0, self.vf, self.neglogp0], {self.input_states:input_states})

    # Function that calculates only the V(s)
    def value(self, input_states):
        return self.sess.run(self.vf, {self.input_states:input_states})

    # Function that output only the action to take
    def select_action(self, input_states):
        return self.sess.run(self.a0, {self.input_states:input_states})
