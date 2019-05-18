
import tensorflow as tf

import utils as ut

class Model(object):
    """
    We use this object to :
    __init__:
    - Creates the step_model
    - Creates the train_model

    train():
    - Make the training part (feedforward and retropropagation of gradients)

    save/load():
    - Save load the model
    """
    def __init__(self, policy, config):

        sess = tf.get_default_session()

        # CREATE THE PLACEHOLDERS
        actions_ = tf.placeholder(tf.int32, [None], name="actions_")
        advantages_ = tf.placeholder(tf.float32, [None], name="advantages_")
        rewards_ = tf.placeholder(tf.float32, [None], name="rewards_")
        lr_ = tf.placeholder(tf.float32, name="learning_rate_")
        # Keep track of old actor
        oldneglopac_ = tf.placeholder(tf.float32, [None], name="oldneglopac_")

        # Keep track of old critic 
        oldvpred_ = tf.placeholder(tf.float32, [None], name="oldvpred_")
        
        # Cliprange
        cliprange_ = tf.placeholder(tf.float32, [])


        # CREATE OUR TWO MODELS
        # Step_model that is used for sampling
        step_model = policy(sess, config, reuse=False)

        # Test model for testing our agent
        #test_model = policy(sess, action_space, 1, 1, reuse=False)

        # Train model for training
        train_model = policy(sess, config, reuse=True)

        # CALCULATE THE LOSS
        # Total loss = Policy gradient loss - entropy * entropy coefficient + Value coefficient * value loss
       
        # Clip the value
        # Get the value predicted
        value_prediction = train_model.vf

        # Clip the value = Oldvalue + clip(value - oldvalue, min = - cliprange, max = cliprange)
        value_prediction_clipped = oldvpred_ + tf.clip_by_value(train_model.vf - oldvpred_,  - cliprange_, cliprange_)

        # Unclipped value
        value_loss_unclipped = tf.square(value_prediction - rewards_)

        # Clipped value
        value_loss_clipped = tf.square(value_prediction_clipped - rewards_)

        # Value loss 0.5 * SUM [max(unclipped, clipped)
        vf_loss = 0.5 * tf.reduce_mean(tf.maximum(value_loss_unclipped,value_loss_clipped ))

        # Clip the policy
        # Output -log(pi) (new -log(pi))
        neglogpac = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=train_model.pi, labels=actions_)
        
        # Remember we want ratio (pi current policy / pi old policy)
        # But neglopac returns us -log(policy)
        # So we want to transform it into ratio
        # e^(-log old - (-log new)) == e^(log new - log old) == e^(log(new / old)) 
        # = new/old (since exponential function cancels log)
        # Wish we can use latex in comments
        ratio = tf.exp(oldneglopac_ - neglogpac) # ratio = pi new / pi old

        # Remember also that we're doing gradient ascent, aka we want to MAXIMIZE the objective function which is equivalent to say
        # Loss = - J
        # To make objective function negative we can put a negation on the multiplication (pi new / pi old) * - Advantages
        pg_loss_unclipped = -advantages_ * ratio 

        # value, min [1 - e] , max [1 + e]
        pg_loss_clipped = -advantages_ * tf.clip_by_value(ratio, 1.0 - cliprange_, 1.0 + cliprange_)

        # Final PG loss
        # Why maximum, because pg_loss_unclipped and pg_loss_clipped are negative, getting the min of positive elements = getting
        # the max of negative elements
        pg_loss = tf.reduce_mean(tf.maximum(pg_loss_unclipped, pg_loss_clipped))

        # Calculate the entropy
        # Entropy is used to improve exploration by limiting the premature convergence to suboptimal policy.
        entropy = tf.reduce_mean(train_model.pd.entropy())

        # Total loss (Remember that L = - J because it's the same thing than max J
        loss = pg_loss - entropy * config.ent_coef + vf_loss * config.vf_coef


        # UPDATE THE PARAMETERS USING LOSS
        # 1. Get the model parameters
        params = ut.find_trainable_variables("model")



        # 2. Calculate the gradients
        grads = tf.gradients(loss, params)
        if config.max_grad_norm is not None:
            # Clip the gradients (normalize)
            grads, grad_norm = tf.clip_by_global_norm(grads, config.max_grad_norm)
        grads = list(zip(grads, params))
        # zip aggregate each gradient with parameters associated
        # For instance zip(ABCD, xyza) => Ax, By, Cz, Da

        # 3. Build our trainer
        trainer = tf.train.RMSPropOptimizer(learning_rate=lr_, epsilon=1e-5)

        # 4. Backpropagation
        _train = trainer.apply_gradients(grads)


        # Train function
        def train(ask_book_env, bid_book_env, inv_env, funds_env, actions,\
            returns, values, neglogpacs, lr, cliprange):
            
            # Here we calculate advantage A(s,a) = R + yV(s') - V(s)
            # Returns = R + yV(s')
            advantages = returns - values

            # Normalize the advantages (taken from aborghi implementation)
            advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)

            # We create the feed dictionary
            td_map = {  train_model.input_ask_book:ask_book_env,
                        train_model.input_bid_book:bid_book_env,
                        train_model.input_inventory:inv_env,
                        train_model.input_funds:funds_env,
                        actions_: actions,
                        advantages_: advantages,
                        rewards_: returns,
                        lr_: lr,
                        cliprange_: cliprange,
                        oldneglopac_: neglogpacs,
                        oldvpred_: values
                     }

            policy_loss, value_loss, policy_entropy, _= sess.run([pg_loss, vf_loss, entropy, _train], td_map)
            
            return policy_loss, value_loss, policy_entropy


        def save(save_path):
            """
            Save the model
            """
            saver = tf.train.Saver()
            saver.save(sess, save_path)

        def load(load_path):
            """
            Load the model
            """
            saver = tf.train.Saver()
            print('Loading ' + load_path)
            saver.restore(sess, load_path)

        self.train = train
        self.train_model = train_model
        self.step_model = step_model
        self.step = step_model.step
        self.value = step_model.value
        # self.initial_state = step_model.initial_state
        self.save = save
        self.load = load
        tf.global_variables_initializer().run(session=sess)
