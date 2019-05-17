
import numpy as np
from baselines.common.runners import AbstractEnvRunner

class Runner(object):
    """
    We use this object to make a mini batch of experiences
    __init__:
    - Initialize the runner

    run():
    - Make a mini batch
    """
    def __init__(self, env, model, config):
        # Lambda used in GAE (General Advantage Estimation)
        self.lam = config.lam
        # Discount rate
        self.gamma = config.gamma

        self.env = env

        self.model = model

        self.nsteps = config.nsteps

        self.obs = env.get_initial_state()

        self.dones = [False for _ in range(config.num_of_envs)]

    def run(self):
        # Here, we init the lists that will contain the mb of experiences
        mb_rewards, mb_actions, mb_values, mb_neglogpacs, mb_dones = [],[],[],[],[]
        mb_ask_book_env, mb_bid_book_env, mb_inv_env, mb_funds_env = [],[],[],[]

        # For n in range number of steps
        for i in range(self.nsteps):
            # Given observations, get action value and neglopacs
            # We already have self.obs because Runner superclass run self.obs[:] = env.reset() on init
            actions, values, neglogpacs = self.model.step(*self.obs)
            mb_ask_book_env.append(self.obs[0])
            mb_bid_book_env.append(self.obs[1])
            mb_inv_env.append(self.obs[2])
            mb_funds_env.append(self.obs[3])
            mb_actions.append(actions)
            mb_values.append(values)
            mb_neglogpacs.append(neglogpacs)
            mb_dones.append(self.dones)
            # Take actions in env and look the results
            # Infos contains a ton of useful informations
            self.obs, rewards, self.dones, time_elapsed = self.env.step(actions)
            if i % 10 == 0:
                print('Runner Progress Count: {0}/{1} | Time: {2}'.format(i, self.nsteps, time_elapsed), end='\r', flush=True)
            mb_rewards.append(rewards)
        #batch of steps to batch of rollouts
        # mb_obs = np.asarray(mb_obs, dtype=np.float32)
        mb_ask_book_env = np.asarray(mb_ask_book_env, dtype=np.float32)
        mb_bid_book_env = np.asarray(mb_bid_book_env, dtype=np.float32)
        mb_inv_env = np.asarray(mb_inv_env, dtype=np.float32)
        mb_funds_env = np.asarray(mb_funds_env, dtype=np.float32)
        mb_rewards = np.asarray(mb_rewards, dtype=np.float32)
        mb_actions = np.asarray(mb_actions)
        mb_values = np.asarray(mb_values, dtype=np.float32)
        mb_neglogpacs = np.asarray(mb_neglogpacs, dtype=np.float32)
        mb_dones = np.asarray(mb_dones, dtype=np.bool)
        last_values = self.model.value(*self.obs)

        # discount/bootstrap off value fn
        mb_returns = np.zeros_like(mb_rewards)
        mb_advs = np.zeros_like(mb_rewards)
        lastgaelam = 0
        for t in reversed(range(self.nsteps)):
            if t == self.nsteps - 1:
                nextnonterminal = 1.0 - self.dones
                nextvalues = last_values
            else:
                nextnonterminal = 1.0 - mb_dones[t+1]
                nextvalues = mb_values[t+1]
            delta = mb_rewards[t] + self.gamma * nextvalues * nextnonterminal - mb_values[t]
            mb_advs[t] = lastgaelam = delta + self.gamma * self.lam * nextnonterminal * lastgaelam
        mb_returns = mb_advs + mb_values
        return map(sf01, (mb_ask_book_env, mb_bid_book_env, mb_inv_env, mb_funds_env,
            mb_returns, mb_actions, mb_values, mb_neglogpacs))

# obs, returns, masks, actions, values, neglogpacs, states = runner.run()
def sf01(arr):
    """
    swap and then flatten axes 0 and 1
    """
    s = arr.shape
    return arr.swapaxes(0, 1).reshape(s[0] * s[1], *s[2:])
