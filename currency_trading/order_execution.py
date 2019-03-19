#!/usr/bin/python
# sub program to close account positions

import time
import numpy as np
from utility_funcs import StochRSI, bullish_candles, bearish_candles, ALMA, RSI, MACD, OBV, NATR

def manage_position(Account, Trade):

	# utility function
	# -------------------------------------------------------------------------
	def flatten(arg):
		flat = []
		for arr in arg:
			for indx in range(len(arr)-8, len(arr)):
				flat.append(arr[indx])
		out = np.array([flat])
		return out

	# convert range of prediction to leverage range
	# -------------------------------------------------------------------------
	def transform(weight, frame):
		mn, mx = Account.lev_range[frame]
		
		OldRange = (1.0 - 0.4)
		NewRange = (mx - mn)
		NewValue = (((weight - 0.4) * NewRange) / OldRange) + mn

		return NewValue[0][0]

	# place an order for given pair
	# -------------------------------------------------------------------------
	def buy(units, pair, frame, close, lev, rg, sig_type):
	
		# look at relative lows
		last_price = close[-1]
		min_price = 1000
		max_price = 0
		l = len(close)

		# find low point for stop loss
		for lookBack in range(1, rg):
			if min_price > close[l-lookBack]:
				min_price = close[l-lookBack]
			if max_price < close[l-lookBack]:
				max_price = close[l-lookBack]

		STOP_LOSS = 0
		# for now, determine stop based on frame
		if frame == "H1" and sig_type == 1:              
			STOP_LOSS = max((last_price*.997), min_price*.998)
		elif frame == "H4" and sig_type == 1:				 
			STOP_LOSS = max((last_price*.988), min_price*.992)
		elif frame == "H1" and sig_type == 0:
			STOP_LOSS = min(((last_price*1.03), max_price*1.02))
		elif frame == "H4" and sig_type == 0:
			STOP_LOSS = min(((last_price*1.15), max_price*1.08))

		try:
			# call order function from main module
			Trade.stop_loss_trade(Account, units, pair, STOP_LOSS, frame, last_price, rg, sig_type)
		except Exception as error:
			print("stop_loss_trade threw an Exception:", error)
			raise Exception("buy() throwing an exception")

	# determine if we should place an order on a waiting pair
	# -------------------------------------------------------------------------
	def buy_sig(weight, op, high, low, close, lev, pair, frame, rg, sig_type):
		orders = 0

		if frame=="H4":
			rsi_level = 55
		else:
			rsi_level = 55

		# determine if a buy signal is met
		fastk, fastd = StochRSI(close)
		signal = False
		if ((fastk[-1] >= fastd[-1]) and (fastk[-1] < rsi_level and close[-1])) and sig_type == 1:
			signal = True
		elif ((fastk[-1] < fastd[-1]) and (fastk[-1] > rsi_level and close[-1])) and sig_type == 0:
			signal = True

		if signal:

			if Trade.can_trade(Account, pair, frame, sig_type):
				Balance = Account.getBalance()
				
				# we are ready to make a trade
				if Balance > 0:
					orders = 1

					# see if there was a bullish candle present
					candle = False
					hammer, engulf, pierce = bullish_candles(op, high, low, close)
					if hammer[-1] > 0 or engulf[-1] > 0 or pierce[-1] > 0 and sig_type == 1:
						candle = True

					# define the leverage based of prediction weight
					leverage = transform(weight, frame)
					Account.avg_lev += leverage
					# if we found reversal candle, increase leverage slightly
					if candle:
						trade_value = (Balance*Account.lev_boost*50)
					else:
						trade_value = (Balance*leverage)*50

					units = trade_value/close[-1]
					buy(units, pair, frame, close, lev, rg, sig_type)
		
		return orders

	# determine if we should close a position
	# -------------------------------------------------------------------------
	def close_sig(op, high, low, close, pair, frame, ID, rg, pos_type):

		if Account == Trade:
				age_acc = 1
		else:
			if frame == "H1":
				age_acc = (24 / Account.data_poll)
			elif frame == "H4":
				age_acc = (6 / Account.data_poll)
	
		Account.age[ID] += age_acc

		# let trade develop
		if Account.age[ID] < (rg - 20):
			return 0

		# collect data for model prediction
		rsi = RSI(close)
		obv = OBV(close, vol)
		natr = NATR(high, low, close)
		aF, aS = ALMA(close)
		stF, stS = StochRSI(close)
		
		# prep data for model prediction
		# predict the whether we should exit or not
		# -------------------------------------------------------------
		ta_data = [close, obv, rsi, aF, aS, stF, stS, natr]
		pred_data = flatten(ta_data)

		# close long positions
		if pos_type == 1:
			if frame == "H1":
				pred_data = Account.H1_SELL_scaler.transform(pred_data)
				prediction = Account.H1_SELL_model.predict(pred_data)

			elif frame == "H4":
				pred_data = Account.H4_SELL_scaler.transform(pred_data)
				prediction = Account.H4_SELL_model.predict(pred_data)

			# close positions if necessary
			if prediction < 0.5 and (aF[-1] < aS[-1] and stF[-1] < stS[-1]):# and Account.age[ID] < rg:
				closed = close_pos(ID, pair, frame, close, 0, pos_type)

			# if age is past range, just look at statistics
			#elif (aF[-1] < aS[-1] and stF[-1] < stS[-1]):
			#	closed = close_pos(ID, pair, frame, close, 0, pos_type)

		# close short positions
		elif pos_type == 0:
			#if frame == "H4":
			if aF[-1] >= aS[-1] and stF[-1] >= stS[-1]:
				closed = close_pos(ID, pair, frame, close, 0, pos_type)


		return 1

	# close a position for given pair
	# -------------------------------------------------------------------------
	def close_pos(ID, pair, frame, close, atempts, pos_type):
		try:
			success = Trade.close_position(Account, ID, pair, frame, close[-1], pos_type)
		except Exception as error:
			if atempts > 5:
				raise Exception("close_pos has not completed order after atempts:")
			else:
				buffer_time = 10       
				time.sleep(buffer_time) # wait 10 seconds
				atempts += 1
				close_pos(ID, pair, frame, close, atempts, pos_type)  # make recursive call to close position

		return 1

	# -------------------------------------------------------------------------
	# see if we need to close any positions
	# -------------------------------------------------------------------------
	closed = 0
	positions = Account.openPositions()
	vol = []
	close = []

	for ID in list(positions):
		pair, frame, pos_type, rg = positions[ID]
		
		try:
			time, vol, op, high, low, close = Account.get_data(frame, pair)
		except Exception as error:
			raise Exception("order_execution/get_data throwing Exception:", error)

		if vol.size == 0:
			continue
	
		try:
			closed += close_sig(op, high, low, close, pair, frame, ID, rg, pos_type)
		except Exception as error:
			raise Exception("order_execution/close_sig throwing Exception:", error)

	# -------------------------------------------------------------------------
	# see if there was a trigger hit
	# -------------------------------------------------------------------------
	orders = 0
	waiting = Account.Waiting()
	
	for key_str in list(waiting):

		# get data for our waiting pair/frame object
		age = waiting[key_str][0]
		pair = waiting[key_str][1]
		frame = waiting[key_str][2]
		sig_type = waiting[key_str][3]
		weight = waiting[key_str][4]
		rg = waiting[key_str][5]
		lev = waiting[key_str][6]

		# we want to add to waiting age but backtest 
		# and trade_control pull data differently
		if Account == Trade:
			age_acc = 1
		else:
			if frame == "H1":
				age_acc = (24 / Account.data_poll)
			elif frame == "H4":
				age_acc = (6 / Account.data_poll)
		
		if age < 3:
			Account.waiting[key_str][0] += age_acc # add to age
		
			try:
				time, vol, op, high, low, close = Account.get_data(frame, pair)
			except Exception as error:
				raise Exception("order_execution/get_data throwing Exception:", error)

			if vol.size == 0:
				continue
			try:
				orders += buy_sig(weight, op, high, low, close, lev, pair, frame, rg, sig_type)
			except Exception as error:
				raise Exception("order_execution/buy_sig throwing Exception:", error)
		
		else:
			Account.end_waiting(key_str)








