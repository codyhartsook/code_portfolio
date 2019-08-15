
from numpy import array
# Imports
import numpy as np
import matplotlib.pyplot as plt
#import gym
#from gym import wrappers

from keras.models import Sequential, Model
from keras.layers import Dense, Conv1D, Activation, Flatten, Input, Concatenate, Dropout, Reshape, LSTM
from keras.optimizers import Adam
from rl.agents.cem import CEMAgent
from rl.memory import EpisodeParameterMemory

from rl.processors import WhiteningNormalizerProcessor
from rl.agents import DDPGAgent, DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
from rl.random import OrnsteinUhlenbeckProcess
from data.data_processor import data_loader
import Trader
import core


data = array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
data = data.reshape((3, 3))
print(data.shape)

y = 1
X = array([data, data, data])

model = Sequential()
model.add(Conv1D(filters=16, kernel_size=2, activation='relu', input_shape=(3, 3)))
model.add(Flatten())
model.add(Dense(16, activation='relu'))
model.add(Dense(1))
model.compile(optimizer='adam', loss='mse')

model.fit(X, y, epochs=1000, verbose=0)
