# how to backtest:
# how to provide data

from Authenticate import Auth
from find_signals import find_signal
from order_execution import manage_position
from utility_funcs import build_df
from sklearn import preprocessing
from sklearn.externals import joblib
from keras.models import load_model
import oandapyV20.endpoints.instruments as instruments
import oandapyV20
import numpy as np
import argparse
from dateutil import rrule
from datetime import datetime, timedelta

import warnings
warnings.filterwarnings("ignore")

# -----------------------------------------------------------------------------
# class Test
# store information for backtesting and provide relative functions
# class test should be replacable for Account and Trade
# -----------------------------------------------------------------------------
class Test():
	
	# initialization and class variables
	# -------------------------------------------------------------------------
	def __init__(self):
		self.account_ID, self.access_token = Auth()
		self.client = oandapyV20.API(access_token=self.access_token)
		
		# set of currency pairs we are interested in
		self.pair_list = ['EUR_USD', 'EUR_GBP', 'USD_CHF', 'GBP_USD', 'USD_JPY', 
						'AUD_USD', 'USD_CAD', 'EUR_JPY', 'EUR_NZD', 'USD_HKD', 'EUR_SGD', 
						'AUD_CAD', 'AUD_CHF', 'AUD_NZD', 'CAD_CHF', 'CAD_JPY', 'CHF_JPY', 
						'EUR_AUD', 'EUR_CAD', 'EUR_CHF', 'GBP_HKD', 'GBP_JPY', 'USD_DKK',
						'USD_THB', 'EUR_CZK']

		# load ml models and scalers to make predictions
		self.H4_BR_model = load_model('H4_DNN_Breakout')
		self.H1_BR_model = load_model('H1_DNN_Breakout')
		self.H4_SELL_model = load_model('H4_SELL_OPT')
		self.H1_SELL_model = load_model('H1_SELL_OPT')
		self.H4_BR_scaler = joblib.load('H4_BR_scaler.save')
		self.H1_BR_scaler = joblib.load('H1_BR_scaler.save')
		self.H4_SELL_scaler = joblib.load('H4_SELL_scaler.save')
		self.H1_SELL_scaler = joblib.load('H1_SELL_scaler.save')

		# position and trade information
		self.open_positions = {} # keep track of open positions
		self.trades = {}         # more specific to trade values
		self.stops = {}          # stop price for given order ID
		self.age = {}
		self.waiting = {}
		self.ml_waiting = {}
		self.ml_data = {}      # ml data for all orders, contains label if order ended in profit
		self.waiting_len = 0
		self.bear_len = 0
		self.stopped = 0
		self.mv_stopped = 0
		self.obv_slope = np.array([])

		self.trade_count = 0   # the current number of trades open
		self.total_trades = 0  # the total number of trades made
		self.last_ID = 0
		self.max_trade_count = 15
		self.balance = 10000
		self.min_balance_reached = 10000
		self.low = 0
		self.losing_tades = {}
		self.worst_trade = {}
		self.worst_trade[0] = '', '', ''
		
		# find optimized leverage
		self.lev_range = {}
		self.lev_range["H4"] = .04, .065
		self.lev_range["H1"] = .03, .055
		self.avg_lev = 0
		self.avg_age = 0
		self.lev_boost = 0.06
		self.margin = 10000
		self.realized_profit = 0

		# data information
		self.lookBack = 0
		self.data = {}
		self.begin = {}
		self.end = {}
		self.init_interval()
		#self.api_date_range_data("H4")

	
	# class methods
	# -------------------------------------------------------------------------
	def init_interval(self):
		for frame in ["H1", "H4", "D"]:
			self.begin[frame] = 0
			self.end[frame] = 60

	# change the way we get data in order to get more candles
	# use from/to notation
	def api_data(self, frame):
		count = 0

		if frame=="H1":
			count = self.lookBack*24
		elif frame=="H4":
			count = self.lookBack*6
		elif frame=="D":
			count = self.lookBack

		params = {
	        "count": count,   
	        "granularity": frame}

		for pair in self.pair_list:
			r = instruments.InstrumentsCandles(instrument=pair, params=params)
			self.client.request(r)   # request data

			time, vol, op, high, low, close = build_df(r)
			self.data[pair] = close, low, high, op, vol, time # hashtable with key=pair, val=candle data

	def datespan(self, startDate, endDate, frame):
		
		delta=timedelta(days=1)
		currentDate = startDate
		while currentDate < endDate:
			yield currentDate
			currentDate += delta

	def duplicate_check(self, pair, Close, Low, High, Opin, Vol, Time):
		last = ""
		to_del = []
		for idx in range(len(Time)):
			if Time[idx] == last:
				to_del.append(idx)
			else:
				last = Time[idx]

		for idx in to_del:
			np.delete(Close, idx)
			np.delete(Low, idx)
			np.delete(High, idx)
			np.delete(Opin, idx)
			np.delete(Vol, idx)
			np.delete(Time, idx)

		self.data[pair] = Close, Low, High, Opin, Vol, Time
		self.lookBack = len(Close)



	def api_date_range_data(self, frame):

		print("< retrieving data, this may take a minute")
		for pair in self.pair_list:

			Time = np.array([])
			Vol = np.array([])
			Opin = np.array([])
			High = np.array([])
			Low = np.array([])
			Close = np.array([])
			
			dat = 'T00:00'
			period = 0
			start = ""
			for timestamp in self.datespan(datetime(2017, 3, 20, 6, 0), datetime(2019, 3, 20, 6, 0), frame):
				if period == 0:
					start = timestamp
				elif period >= 82:
					b = str(start).split(" ")[0]+dat
					e = str(timestamp).split(" ")[0]+dat
					print(b, " - ", e)

					# request data
					params = {
					"from": b,
					"to": e,
					"granularity": frame}

					r = instruments.InstrumentsCandles(instrument=pair, params=params)
					self.client.request(r)

					time, vol, op, high, low, close = build_df(r)
					Time = np.append(Time, time)
					Vol = np.append(Vol, vol)
					Opin = np.append(Opin, op)
					High = np.append(High, high)
					Low = np.append(Low, low)
					Close = np.append(Close, close)

					self.duplicate_check(pair, Close, Low, High, Opin, Vol, Time)
					#self.data[pair] = Close, Low, High, Opin, Vol, Time
					start = timestamp
					period = 0
				period += 1
			print(len(Close))
	
	# interacts with find_signals
	def get_data(self, frame, pair):
		close, low, high, op, vol, time = self.data[pair]
		if self.end[frame] >= len(vol)-1: #specific to D, need to change
			empty = np.array([])
			return empty, empty, empty, empty, empty, empty

		# cant slice candles data
		time_ = time[self.begin[frame]:self.end[frame]]
		vol_ = vol[self.begin[frame]:self.end[frame]]
		open_ = op[self.begin[frame]:self.end[frame]]
		high_ = high[self.begin[frame]:self.end[frame]]
		low_ = low[self.begin[frame]:self.end[frame]]
		close_ = close[self.begin[frame]:self.end[frame]]

		return time_, vol_, open_, high_, low_, close_

	def update_data(self, frame):
		self.begin[frame] += 1
		self.end[frame] += 1

	# intacts with manage_positions
	# return hashtable of open positions
	def openPositions(self):
		return self.open_positions

	def possible_trade(self, pair, frame, sig_type, prediction, rg, o_slope, p_slope, obv, cycle, lev):
		waiting_str = pair+","+frame
		self.waiting[waiting_str] = [0, pair, frame, sig_type, prediction, rg, lev]
		self.waiting_len += 1

	def Waiting(self):
		return self.waiting

	# interacts with find_signals
	def getBalance(self):
		return self.margin

	# interacts with find_signals
	# see if we already have the trade
	def can_trade(self, Account, pair, frame, sig_type):
		trade_count = self.trade_count
		if trade_count >= self.max_trade_count:
			return False

		positions = self.openPositions()
		for ID in positions:
			open_pair, open_frame, pos_type, rg = positions[ID]
			
			open_pair = open_pair.strip()
			open_frame = open_frame.strip()
			pair = pair.strip()
			frame = frame.strip()


			if open_pair==pair and open_frame==frame and sig_type == pos_type:
				return False
		return True

	def end_waiting(self, w_str):
		del self.waiting[w_str]
		#del self.ml_waiting[w_str]

	# set the buy price of pair: trades[ID] = currprice, units
	# set the stop price for pair: stops[pair] = stop_price
	# set open_positions[pair] = ID, frame: generate ID, last_ID+1
	# update balance
	def stop_loss_trade(self, Account, units, pair, stop_price, frame, last_price, rg, sig_type):
		ID = self.last_ID + 1
		self.last_ID += 1

		#self.ml_data[ID] = self.ml_waiting[pair+","+frame]
		#self.ml_data[ID] = np.insert(self.ml_data[ID], 0, ID, axis=0)

		self.trades[ID] = last_price, units
		self.open_positions[ID] = pair, frame, sig_type, rg
		self.stops[ID] = stop_price
		self.trade_count += 1
		self.total_trades += 1

		time, vol, op, high, low, close = self.get_data(frame, pair)
		if close[-1] != last_price:
			print(close[-1], " -- ", last_price)
			print("ERROR")
			exit()

		print("< BUY ORDER:------------------------------------------------")
		print("< trade placed at", time[-1])
		print("< pair:", pair, " -- frame:", frame)
		print("< long/short:", sig_type)
		print("< order price:", last_price)
		print("< stop_price:", stop_price)
		print("------------------------------------------------------------")

		self.margin = (self.balance - (units*last_price)/50)
		self.age[ID] = 0

	# manage all stop losses
	def manage_stops(self):
		for ID in list(self.open_positions):
			pair, frame, sig_type, rg = self.open_positions[ID]
			stop_p = self.stops[ID]
			end_interval = self.end[frame]-1
			close, low, high, op, vol, time = self.data[pair]
			curr_p = close[end_interval]

			if curr_p <= stop_p:
				self.close_position(self, ID, pair, frame, curr_p, sig_type)
				self.stopped += 1

	# interacts with manage_positions
	# add to realized profit by calling update profit
	# delete positions[pair], trades[pair], stops[pair]
	def close_position(self, Account, ID, pair, frame, last_price, pos_type):
		
		pair, frame, pos_type, rg = self.open_positions[ID]
		time, vol, op, high, low, close = self.get_data(frame, pair)

		if last_price != close[-1]:
			print("ERROR---------------------------")

		b_price, units = self.trades[ID]
		val1 = b_price*units
		val2 = last_price*units
		self.avg_age += self.age[ID]

		# long position
		if pos_type == 1:
			self.realized_profit += (val2-val1) # add to profit, could be negative
			self.balance += (val2-val1)
		# short position
		else:
			self.realized_profit = (val1-val2)
			self.balance += (val1-val2)

		self.trade_count -= 1
		self.margin = self.balance
		self.mv_stopped += 1

		if self.balance < self.min_balance_reached:
			self.min_balance_reached = self.balance
			self.low = self.total_trades

		if (val2-val1) < 0 and pos_type == 1:
			self.losing_tades[ID] = time[-1], pair, frame
		elif (val1 - val2) < 0 and pos_type == 0:
			self.losing_tades[ID] = time[-1], pair, frame

		print("< CLOSE ORDER:----------------------------------------------")
		print("< order placed at", time[-1])
		print("< pair:", pair, " -- frame:", frame)
		print("< close price:", last_price)
		print("------------------------------------------------------------")

		del self.trades[ID]
		del self.open_positions[ID]
		del self.stops[ID]
		del self.age[ID]

	def init_write(self):
		open('sell_time.csv', 'w').close()
		with open('sell_time.csv', 'a') as f_writer:
			
			ln = "ID,rg,h,l,c1,c2,c3,supp,o_s,p_s,obv1,obv2,obv3,rsi1,rsi2,rsi3,natr,cyc,stF,stS,rsi,obv,natrF,alF, alS,fC\n"
			f_writer.write(ln)
			f_writer.close()
	
	def write_data(self, ID, data):
		with open('sell_time.csv', 'a') as f_writer:
			
			ln = str(ID) + ","
			for item in data:
				if item == data[-1]:
					ln += str(item) + "\n"
				else:
					ln += str(item) + ","

			f_writer.write(ln)
			f_writer.close()

	# print account summary
	def account_summary(self):
		print("\nTotal trades:", self.total_trades)
		print("Realized profit:", self.realized_profit)
		print("Account value:", self.balance)
		if self.total_trades == 0:
			print("Trade num to profit ratio: 0")
		else:
			print("Trade num to profit ratio:", self.realized_profit/self.total_trades)
		print("Return %:", (self.realized_profit/10000)*100)
		
		print("Open positions:", self.trade_count)
		pos_val = 0
		for ID in list(self.open_positions):
			#print("open position")
			pair, frame, pos_type, rg = self.open_positions[ID]
			close, low, high, op, vol, time = self.data[pair]
			last_price = close[-1]

			b_price, units = self.trades[ID]
			#print("buy price:", b_price, " | last price: ", last_price)
			val1 = b_price*units
			val2 = last_price*units
			pos_val += (val2-val1)

		print("Position value:", pos_val)
		print("Stopped trades:", self.stopped)
		print("Closed trades:", self.mv_stopped)
		print("Number of possible trades:", self.waiting_len)
		print("bear signals:", self.bear_len)
		print("Min account balance:", self.min_balance_reached)
		print("avg age:", self.avg_age / self.total_trades)
		print("Reached after", self.low, "trades")
		print("Negative trade count:", len(self.losing_tades))
		print("average leverage:", self.avg_lev / self.total_trades)
		print("Negative trades:")
		for ID in self.losing_tades:
			time, pair, frame = self.losing_tades[ID]
			print(pair, "-", frame, " at ", time)




# -----------------------------------------------------------------------------
# program execution starts
# look for buy and selling signals then sleep 
# -----------------------------------------------------------------------------
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='backtest')
	parser.add_argument('--frame', required=True, dest="frame", metavar='NAME', 
		help='Which chart time to test: H1; H4; D')

	args = parser.parse_args() 
	chart_time = args.frame

	TEST = Test() # get an instance of the test class

	print("/////////////////////////////////////////////////////////////////////////")
	print("// initializing backtesting program")
	print("// look back is", TEST.lookBack, "days")
	print("/////////////////////////////////////////////////////////////////////////\n")

	TEST.init_write()

	if chart_time == "H1":
		# run backtest for highest frequency chart time
		print("< running backtest on H1 candles")
		#TEST.api_data("H1")  
		TEST.api_date_range_data("H1")              # update the price data 
		length = (TEST.lookBack*24 - 60)  # hourly candles * 24 to get day
		for itr in range(0, length):
			find_signal(TEST, TEST, "H1") # pass frame as parameter
			TEST.manage_stops()
			manage_position(TEST, TEST)
			TEST.update_data("H1")

		print("< backtest complete, print account summary:")
		print("-------------------------------------------------------------------------")
		TEST.account_summary()

	elif chart_time == "H4":
		# run backtsest for medium frequency chart time
		print("< running backtest on H4 candles")
		#TEST.api_data("H4")
		TEST.api_date_range_data("H4")               # update the price data
		length = (TEST.lookBack - 60)  # 4 hour candles * 6 to get day
		print("< number of candles:", length, "\n")
		for itr in range(0, length):
			find_signal(TEST, TEST, "H4") # pass frame as parameter
			TEST.manage_stops()
			manage_position(TEST, TEST)
			TEST.update_data("H4")

		print("< backtest complete, print account summary:")
		print("-------------------------------------------------------------------------")
		TEST.account_summary()

	elif chart_time == "D":
		# run backtest for lowest frequency chart time
		print("< running backtest on D candles")
		TEST.api_data("D")               # update the price data
		length = (TEST.lookBack - 60)    # daily candles
		for itr in range(0, length):
			find_signal(TEST, TEST, "D") # pass frame as parameter
			TEST.manage_stops()
			manage_position(TEST, TEST)
			TEST.update_data("D")

		print("< backtest complete, print account summary:")
		print("-------------------------------------------------------------------------")
		TEST.account_summary()




