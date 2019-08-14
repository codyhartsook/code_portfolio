# DRL Program: Actor-Critic RL Algorithm implemented for currency trading


# Imports
import numpy as np
import matplotlib.pyplot as plt
#import gym
#from gym import wrappers

from keras.models import Sequential, Model
from keras.layers import Dense, Activation, Flatten, Input, Concatenate, Dropout
from keras.layers import Conv1D, MaxPooling1D, GlobalAveragePooling1D, Reshape, LSTM
from keras.layers.normalization import BatchNormalization
from keras.optimizers import Adam
from rl.agents.cem import CEMAgent
from rl.memory import EpisodeParameterMemory

from keras.callbacks import ReduceLROnPlateau
from rl.processors import WhiteningNormalizerProcessor
from rl.callbacks import CallbackList, TrainIntervalLogger
from rl.agents import DDPGAgent, DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess
from data.data_processor import data_loader
import Trader
import core

import warnings
warnings.filterwarnings("ignore")

#
#
# -------------------------------------------------------------------------------------------------

# blueprint for small actor model
# ONCE IMPLEMENTED, TEST CNN AND LSTM
def build_actor(env, nb_actions, features, window):
	input_shape = env.observation_space.shape[0]
	
	actor = Sequential()
	actor.add(LSTM(128, input_shape=(1, input_shape), return_sequences=True))
	actor.add(Activation('relu'))
	actor.add(Dropout(.4))
	actor.add(LSTM(128))
	actor.add(Activation('relu'))
	actor.add(Dropout(.4))
	actor.add(Dense(64))
	actor.add(Activation('relu'))
	actor.add(Dropout(.2))
	actor.add(Dense(nb_actions))
	actor.add(Activation('linear'))

	return actor

# blueprint for small critic model
def build_critic(action_input, observation_input, flattened_observation):
	x = Concatenate()([action_input, flattened_observation])
	x = Dense(64)(x)
	x = Activation('relu')(x)
	x = Dropout(0.4)(x)
	x = Dense(128)(x)
	x = Activation('relu')(x)
	x = Dropout(0.4)(x)
	x = Dense(64)(x)
	x = Activation('relu')(x)
	x = Dropout(0.2)(x)
	x = Dense(1)(x)
	x = Activation('linear')(x)
	critic = Model(inputs=[action_input, observation_input], outputs=x)

	return critic

def analyze_results(ENV, history):

	print("positive trades:", ENV.pos_trades)
	print("negative trades:", ENV.neg_trades)
	print("level:", ENV.level)

	plt.plot(ENV.STATS['RPE'])
	plt.ylabel("RPE")
	plt.show()

	plt.hist(ENV.STATS['RPE'], normed=True, bins=30)
	plt.ylabel('RPE hist')
	plt.show()

	plt.plot(history.history['episode_reward'])
	plt.ylabel("episode_reward")
	plt.show()

	#plt.plot(ENV.STATS['PT'])
	#plt.ylabel('PT')
	#plt.show()

	#plt.plot(ENV.STATS['NT'])
	#plt.ylabel('NT')
	#plt.show()

	plt.hist(ENV.STATS['DUR'])
	plt.ylabel('Duration')
	plt.show()

# 
# Main
# -------------------------------------------------------------------------------------------------
if __name__ == "__main__":

	
	data_obj = data_loader("save_file")
	SPACE = core.Space(data_obj)
	BROKER = Trader.Trade()
	ENV = core.Env(SPACE, BROKER)
	ENV_NAME = 'Trade_rl-v1'

	# action space
	nb_actions = len(ENV.action_space)
	dataset_len = data_obj.length
	features = SPACE.features
	obs_length = ENV.look_ahead
	print("nb_actions", nb_actions)
	print("obs shape:", ENV.observation_space.shape[0])

	# keras memory

	# DDPG
	memory = SequentialMemory(limit=500000, window_length=1)
	action_input = Input(shape=(nb_actions,), name='action_input')	
	observation_input = Input(shape=(1,) + ENV.observation_space.shape, name='observation_input')
	flattened_observation = Flatten()(observation_input)
	random_process = OrnsteinUhlenbeckProcess(size=nb_actions, theta=.15, mu=0., sigma=.1)

	# build actor model
	actor = build_actor(ENV, nb_actions, features, obs_length)

	# build critic model
	critic = build_critic(action_input, observation_input, flattened_observation)

	# build RL agent
	agent = DDPGAgent(nb_actions=nb_actions, actor=actor, critic=critic, critic_action_input=action_input,
                  memory=memory, nb_steps_warmup_critic=100, nb_steps_warmup_actor=100, batch_size=32,
                  random_process=random_process, gamma=.99, target_model_update=1e-3)
	
	# compile agent
	agent.compile([Adam(lr=1e-4), Adam(lr=1e-4)], metrics=['mae', 'acc'])
	
	# train agent
	#reduce_lr = ReduceLROnPlateau(monitor='episode_reward', factor=0.2, patience=5, min_lr=0.001)
	#rl_callback = CallbackList([reduce_lr])
	checkpoint_weights_filename = 'model_weights/ddpg_' + ENV_NAME + '_weights_{step}.h5f'
	callbacks = [TrainIntervalLogger(interval=1000)]
	#callbacks += [ModelIntervalCheckpoint(checkpoint_weights_filename, interval=2500)]

	STEPS = 20000
	history = agent.fit(ENV, nb_steps=STEPS, visualize=False, verbose=1, callbacks=callbacks)

	# history keys: dict_keys(['episode_reward', 'nb_episode_steps', 'nb_steps'])
	print(history.history.keys())
	analyze_results(ENV, history)

	











