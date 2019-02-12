#!/usr/bin/python
# sub program to find buying opportunities

# imports
import numpy as np
import math
from utility_funcs import NATR, OBV, RSI

def find_signal(Account, Trade, Frame):

	# uses the Deep Neural Net to make a prdiction
	def find_sig2(high, low, close, OBV_in, pair, frame):
		
		# normalize obv in order to filter min slope
		maxv = max(OBV_in)
		minv = min(OBV_in)
		sc = max(abs(minv), maxv)
		OBV = [(x+sc+1)/sc for x in OBV_in]

		#scaler = preprocessing.MinMaxScaler()
		#obv = scaler.fit_transform(obv)

		for rg in range(28, 60):
			begin = (len(close) - rg)
			end = len(close)
	
			# slice arrays by interval rg to length
			pr = np.array(close[begin:end])
			obv = np.array(OBV[begin:end])

			sig, lev = dual_troughs(pr)
			if sig:
				
				p_slope = slope(pr)           # slope of price
				o_slope = slope(obv)          # slope of obv
				rsi = RSI(pr)                 # rsi of price
				natr = NATR(high, low, close) # volatility
				cycle_change = swing(close)   # price cycle range
				rang = end - begin

				if (cycle_change > 1.06) and (o_slope > 0):

					# add data to possible breakout
					pred_data = np.array([[rang, high[-1], low[-1], close[-1],
							close[len(close)-2], close[len(close)-3], lev, o_slope, 
							p_slope, obv[-1], obv[len(obv)-2], obv[len(obv)-3], 
							rsi[-1], rsi[len(rsi)-2], rsi[len(rsi)-3], natr[-1], 
							cycle_change]])

					# scale the data with the same scaler used in training
					pred_data = Account.scaler.transform(pred_data)
					# make a prediction using the ml model
					prediction = Account.model.predict(pred_data)

					if prediction > 0.5:

						# store pair/frame and relevant statistics to see if we want to buy later
						#Account.ml_buy(pair, frame)
						Account.possible_trade(pair, frame, False, rang, o_slope, p_slope, obv[-1], cycle_change, lev)
						return True, 1, 1
	
	# find slope in order to determine diveregence
	# compute slope value for all ranges length-rg
	# -----------------------------------------------------------------------------
	def find_sig(high, low, close, OBV_in, pair, frame):
		
		# normalize obv in order to filter min slope
		maxv = max(OBV_in)
		minv = min(OBV_in)
		sc = max(abs(minv), maxv)
		OBV = [(x+sc+1)/sc for x in OBV_in]

		for rg in range(28, 60):
			begin = (len(close) - rg)
			end = len(close)
	
			# slice arrays by interval rg to length
			pr = np.array(close[begin:end])
			obv = np.array(OBV[begin:end])
			
			sig, lev = dual_troughs(pr)
			if sig:
				
				p_slope = slope(pr)
				o_slope = slope(obv)

				# we want there to be volatility
				cycle_change = swing(close)
				mx = max(obv)
				diff = mx - obv[-1]
				delta = (diff / obv[-1] * 100)
				# This is the filter for possible trades:
				if (o_slope > 0) and (p_slope < 0) and (obv[0] < obv[-1]) and (cycle_change > 1.065):
					
					# store pair/frame and relevant statistics to see if we want to buy later
					Account.possible_trade(pair, frame, True, rg, o_slope, p_slope, obv[-1], cycle_change, lev)
					return True, 1, 1

		return False, 0, 0 # did not find a divergence

	# compute the slope using np.polyfit with order 1
	def slope(y):
		x = range(0, len(y))
		coeffs = np.polyfit(x, y, 1)

		intercept = coeffs[-1]  # might use this in ordering weight
		slope = coeffs[-2]

		return slope

	# see if it is volatile enough to trust divergence
	def volatility(frame, high, low, close):
		natr = NATR(high, low, close)
		
		hard_val = 0

		if frame=="H1":
			hard_val = 0.12
		elif frame=="H4":
			hard_val = 0.18
		elif frame=="D":
			hard_val = 0.7

		return (natr[-1] > hard_val)

	# look at the percent difference between high and low price in interval
	def swing(close):
		MAX = max(close)
		MIN = min(close)

		diff = MAX - MIN
		delta = (diff / MIN * 100)

		return delta

	# determine of price is in a trough for given interval
	def trough(close):
		mn = min(close)
		return (mn==close[-1])

	# find dual troughs: right now dont care which trough is lower
	# this will ensure that there is support for the trade
	# we also want to make sure that there is price change between the lows
	def dual_troughs(close):
		cl_len = len(close)

		first = second = 1000 # smallest, 2nd smallest = value > any currency
		f_index = s_index = 0

		for i in range(0, cl_len): 
  
		    # If current element is smaller than first then 
		    # update both first and second 
			if close[i] < first: 
				second = first 
				first = close[i]
				f_index = i

		    # If arr[i] is in between first and second then 
		    # update second 
			elif (close[i] < second and close[i] != first): 
				second = close[i]
				s_index = i

		if (first == close[-1] or second == close[-1]):
			
			T_diff = second - first
			T_delta = (T_diff / first) * 100

			interval = close
			if f_index > s_index:
				interval = close[s_index:f_index]
			else:
				interval = close[f_index:s_index]

			mx = max(interval)
			I_diff = mx - ((first + second) / 2)
			I_delta = (I_diff / ((first + second) / 2)) * 100

			if I_delta > 0.15 and T_delta < 0.15:
				return True, second
		
		return False, 0

	# execution starts here
	# -----------------------------------------------------------------------------
	# oanda account
	access_token = Account.access_token
	client = Account.client

	# list of current assets
	orders = 0

	# iterate through all forex pairs
	pair_list = ['EUR_USD', 'EUR_GBP', 'USD_CHF', 'GBP_USD', 'USD_JPY', 
		'AUD_USD', 'USD_CAD', 'EUR_JPY', 'EUR_NZD', 'USD_HKD', 'EUR_SGD', 
		'AUD_CAD', 'AUD_CHF', 'AUD_NZD', 'CAD_CHF', 'CAD_JPY', 'CHF_JPY', 
		'EUR_AUD', 'EUR_CAD', 'EUR_CHF', 'GBP_HKD']

	for pair in pair_list:

		# get api data
		time, vol, op, high, low, close = Account.get_data(Frame, pair)

		if close.size == 0:
			break
		
		# get statistics
		obv = OBV(close, vol)

		# find slopes and divergencies
		find_sig2(high, low, close, obv, pair, Frame)
		#find_sig(high, low, close, obv, pair, Frame)











