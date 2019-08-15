from copy import deepcopy
import random 

import numpy as np
from scipy.interpolate import interp1d
from keras.callbacks import History
import gym
from gym.spaces import Discrete, Tuple, Box
from gym.utils import EzPickle
from sklearn.preprocessing import MinMaxScaler

from rl.callbacks import (
    CallbackList,
    TestLogger,
    TrainEpisodeLogger,
    TrainIntervalLogger,
    Visualizer
)
import warnings
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt

class Env(gym.Env, EzPickle):
    
    # Only promote/increase min_episode_trades if the worst of the
    # last n episodes was no more than this far from the maximum reward
    MIN_REWARD_SHORTFALL_FOR_PROMOTION = -1 # this far from max reward

    # MY OVERRIDE FOR CURRENCY TRADING
    def __init__(self, SP, Trader):
        
        gym.Env.__init__(self)      
        #self.log = create_logger('env_logger', loglevel)

        # settings and class instances
        self.Space_Instance = SP
        self.Trader_Instance = Trader
        self.last_action = -1
        self.look_ahead = 50
        self.current_step = 0
        self.done = False
        self.state = -1
        self.DIRECTIONS = 2
        self.MAX_DURATION = 2
        
        # stats
        self.pos_trades = 0
        self.neg_trades = 0
        self.episode_total_reward = 0
        self.STATS = {'RPE':[], 'PT':[], 'NT':[], 'DUR':[]}
        self.level = 0
        
        # internal env/market
        self.reward_shortfalls = []
        self.market = self.Space_Instance.sample(self.look_ahead*4)
        self.candle_window = [0, self.look_ahead]  # each step has a window of 10 candles
        self.epsilon = 1
        self.trend = []

        # action space: 
        # 0 = short, 1 = long
        # 0 = close, 1 = hold/nothing
        self.action_space = Tuple((Discrete(self.DIRECTIONS), Discrete(self.MAX_DURATION)))
        self.observation_space = self.Space_Instance.obs_space(self.look_ahead)
        self.max_episode_steps = 50
        self.required_winning_trades = 2
        self.counter = 0
        self.max_level = 5
        self.LEVEL_UP = 0

        # rewards
        self.time_exp = -1
        self.losing_trade = -0.25
        self.winning_trade = 1
        
        self.max_reward = 20     # for trade closout normalization
        self.min_reward = -0.25
        
        self.reset()

    # Algorithm to determine if we should level up
    def _check_levelup(self):
        
        if self.episode_total_reward is None:
            # This is before the first episode/call to reset(). Nothing to do
            return
        
        if (self.LEVEL_UP >= 4) and (self.required_winning_trades < self.max_level):
            self.required_winning_trades += 1
            self.LEVEL_UP = 0
            self.losing_trade += (-0.25)
            self.level += 1
            #print("WE LEVELED UP")

    def reset(self):
        """
        Resets the state of the environment and returns an initial observation.
        # Returns
            observation (object): The initial observation of the space. Initial reward is assumed to be 0.
        """
        self._check_levelup()
        self.episode_total_reward = 0
        self.done = False
        self.candle_window = [0, self.look_ahead]
        self.last_reward = 0
        self.state = 0
        self.counter = 0
        self.last_action = -1
        self.done = False
        self._finish_on_next_step = False

        self.market = self.Space_Instance.sample(self.look_ahead*4)
        obs = self._get_obs()

        return obs

    def normalize_reward(self, episode_reward):
        """
        since trades will produce small profit without leverage, scale profit 
        according to window range
        """

        if episode_reward == 0:
            return self.losing_trade

        print("\nreward in:", episode_reward)

        st = self.candle_window[0]
        en = self.candle_window[1]

        cycle_max = max(self.market['Close'].as_matrix())
        cycle_min = min(self.market['Close'].as_matrix())

        scaler = (self.max_reward + (cycle_max - cycle_min))
        if episode_reward < 0:
            self.neg_trades += 1
            new_reward = (episode_reward + self.losing_trade + (self.state / 10))

        else:
            new_reward = (episode_reward * scaler + self.winning_trade + ((self.state*2) / 10))
            self.pos_trades += 1

        print("reward out:", new_reward)
        print("duration of trade:", self.state, "\n")

        return new_reward

    def price_at_index(self, index):
        try:
            price = self.market.iloc[index]['Close']
            return price
        except IndexError:
            print("warning: calling step() even though env has returned done")
            self.finish_on_next_step()
            return self.market.iloc[0]['Close']

    def finish_on_next_step(self):
        self._finish_on_next_step = True

    def extract_action(self, action):
        direc, dur = action

        direc = np.clip(direc, 0, self.DIRECTIONS)
        dur = np.clip(dur, 0, self.MAX_DURATION)
        direc = int(round(np.asscalar(direc)))
        dur = int(round(np.asscalar(dur)))

        return direc, dur

    def explore(self, action):

        if (self.current_step % 1000 == 0): # needs emprovement
            print("changing epsilon")
            self.epsilon = 1

        rand = np.random.random() #[0, 1]
        if rand < self.epsilon:
            self.epsilon += (-0.001)
            act = random.randint(1, self.MAX_DURATION+1)
            self.state = act
            return act
        else:
            return action

    def step(self, action):
        
        self.current_step += 1
        if (self.current_step % 500 == 0):
            print("\nlast reward:", self.last_reward)

        oldest = self.candle_window[0]
        latest = self.candle_window[1]

        # took too many steps to make a trade
        if (oldest >= self.max_episode_steps) or self._finish_on_next_step:
            done = True
            observation = np.zeros(self.observation_space.shape)
            reward = self.time_exp
            self.STATS['RPE'].append(self.episode_total_reward)
            self.STATS['PT'].append(0)
            self.STATS['NT'].append(0)
            self.state = 0
            return observation, reward, done, {}
        
        step_reward = 0
        done = False
        info = {} 
        last_price = self.price_at_index(latest)

        direction, duration = self.extract_action(action) 
        duration = self.explore(duration)

        
        # we are in trade for duration candles
        if duration > 0:
            # enter trade or continue trade
            self.Trader_Instance.place_trade(direction, last_price)

            for in_trade in range(0, duration):
                self.state += 1
                self.candle_window[0] += 1
                self.candle_window[1] += 1

            self.STATS['DUR'].append(self.state)

        else:
            profit = self.Trader_Instance.place_trade(4, last_price)
            step_reward += self.normalize_reward(profit)
            self.state = 0

        self.last_reward = step_reward
        self.last_action = action
        self.episode_total_reward += step_reward

        observation = self._get_obs()
        if step_reward > 0:
            self.STATS['RPE'].append(self.episode_total_reward)
            self.STATS['PT'].append(1)
            self.STATS['NT'].append(0)
            done = True
            if self.counter >= self.required_winning_trades:
                print("counter > 2")
                print("step_reward:", step_reward)
                self.counter = 0
                self.LEVEL_UP += 1
            else:
                self.counter += 1

        elif step_reward < 0:
            done = True
            observation = np.zeros(self.observation_space.shape)
            self.STATS['PT'].append(0)
            self.STATS['NT'].append(1)

            if self.LEVEL_UP > 0:
                self.LEVEL_UP += (-1)

        return observation, step_reward, done, info

    def normalize_obs(self, obs):
        scaler = MinMaxScaler()
        obs = np.array(obs).reshape(-1,1)
        norm = scaler.fit_transform(obs)
        norm = np.ravel(norm)
        return norm

    def _get_obs(self):
        prev = self.candle_window[0]
        curr = self.candle_window[1]
        self.candle_window[0] += 1
        self.candle_window[1] += 1

        flat_mrk = []
        for col in self.market.columns:
            
            column = self.market[col].as_matrix()
            column = self.normalize_obs(column[prev:curr])
            flat_mrk.append(column)

        #obs = scaled.ravel()
        obs = np.append(flat_mrk, self.state)

        return obs

    def _render(self):
        raise NotImplementedError()

    def close(self):
        
        self.done = True
        #print("Env.close() not implemented")
        #raise NotImplementedError()

    def seed(self, seed=None):
        """Sets the seed for this env's random number generator(s).
        # Returns
            Returns the list of seeds used in this env's random number generators
        """
        raise NotImplementedError()

    def __del__(self):
        self.close()

    def __str__(self):
        return '<{} instance>'.format(type(self).__name__)


# Note: the API of the `Env` and `Space` classes are taken from the OpenAI Gym implementation.
# https://github.com/openai/gym/blob/master/gym/core.py

class Space(Discrete):

    """Abstract model for a space that is used for the state and action spaces. This class has the
    exact same API that OpenAI Gym uses so that integrating with it is trivial.
    Please refer to [Gym Documentation](https://gym.openai.com/docs/#spaces)
    """

    def __init__(self, data_loader):
        # different datasets for different base pairs
        self.space1 = data_loader.get_data("H1", "EUR_USD")
        self.space2 = None
        self.space3 = None
        self.space4 = None
        self.length = len(self.space1.index)

        self.spaces = {1:self.space1, 2:self.space2, 3:self.space3, 4:self.space4}
        self.curr_sample = None
        self.features = 0
        print("length of space:", len(self.space1.index))

    def sample(self, length):
        """Uniformly randomly sample a random element of this space.
        """

        upper_bound = self.length 
        rand_lower = random.randint(0, (upper_bound-length))
        #base_pair = random.randint(1, 4)
        base_pair = 1

        rand_upper = rand_lower + length
        #print("lower_bound:", rand_lower)
        #print("upper_bound:", rand_upper)
        sample_df = self.spaces[base_pair][rand_lower:rand_upper]
        sample_df = sample_df.reset_index(drop=True)

        #sample = sample_df['Close'].as_matrix() # convert to ndarray
        self.curr_sample = sample_df
        self.features = len(self.curr_sample)

        return sample_df

    def obs_space(self, window_len):

        try:
            window = self.curr_sample[0:window_len]
            flat = np.append(window.values.flatten(), 1)
            return flat
        except:
            raise Exception ("obs_space being called before sample()")

    def contains(self, x):
        """Return boolean specifying if x is a valid member of this space
        """
        raise NotImplementedError()