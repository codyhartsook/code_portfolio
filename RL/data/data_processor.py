# dataloader module

import math
import numpy as np
import pandas as pd
import talib as ta
import matplotlib.pyplot as plt

import oandapyV20
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.accounts as accounts
from oandapyV20.exceptions import V20Error
from data import utils
from data.Authenticate import Auth

import warnings
warnings.filterwarnings("ignore")

class data_loader():
	def __init__(self, filename):
		self.dataframe = None
		self.length = 0
		self.shape = None
		self.initialized = False
		self.account_ID, self.access_token = Auth()
		self.client = oandapyV20.API(access_token=self.access_token)

	def get_data(self, frame, pair):
		#try:
		#	self.dataframe = pd.read_csv(filename)
		#except:
		self.load_data(frame, pair)

		return self.dataframe

    # normalize columns of dataframe
	def normalize(self):
		pass

    # perform technical analysis and add to dataframe
	def add_ta(self):
		#self.dataframe = utils.HA(self.dataframe) # add candles
		self.dataframe['RSI'] = utils.RSI(self.dataframe)
		self.dataframe['OBV'] = utils.OBV(self.dataframe)
		#self.dataframe['ATR'] = utils.NATR(self.dataframe)
		self.dataframe = self.dataframe.dropna()
		self.shape = self.dataframe.shape

	def translate(self, last_date, date):
		fr = (str(last_date).split(" ")[0]) + 'T00'
		to = (str(date).split(" ")[0]) + 'T00'
		return fr, to

	def check_dups(self):
		times = self.dataframe['Time'].as_matrix()
		last_t = times[0]
		
		for t in times:
			if t == times[0]:
				continue 

			if t == last_t:
				print("error, found dups", t, " --- ", last_t)

			last_t = t

    # load oanda data
	def load_data(self, frame, pair):
		pair_list = [pair]

		# create a series of dates
		dates = pd.Series(pd.date_range('2014', freq='M', periods=36)) 
		last_date = dates[0]

		for date in dates:
			if date == dates[0]:
				continue

			from_d, to_d = self.translate(last_date, date)	
			
			params = {
				"from": from_d,
				"to": to_d,         
				"granularity": frame}   # time frame


			r = instruments.InstrumentsCandles(instrument=pair, params=params)
			self.client.request(r)

			if self.initialized != False:
				self.dataframe = self.dataframe.append(utils.build_df(r), ignore_index = True)
			else:
				self.dataframe = utils.build_df(r)
				self.initialized = True

			self.shape = self.dataframe.shape
			last_date = date

		self.add_ta()
		self.check_dups()
		self.length = len(self.dataframe.index)
		self.dataframe = self.dataframe.drop(columns=['Time', 'High', 'Low', 'Open'])

# test the class
if __name__ == "__main__":
	dt_load = data_loader("cwd")
	dt_load.get_data("H1", "EUR_USD")
	#dt_load.load_data("H1", "EUR_USD")
	print("dataset features:", len(dt_load.dataframe.columns))
	print("dataset length:", dt_load.length)
	print("dataset shape:", dt_load.shape)







