#!/usr/bin/python
# sub program to close account positions

import time
import datetime
import numpy as np
from utility_funcs import StochRSI, bullish_candles, bearish_candles, ALMA, RSI, MACD, OBV, NATR

def manage_position(Account, Trade, logger):

	# utility function
	# -------------------------------------------------------------------------
	def flatten(arg):
		flat = []
		for arr in arg:
			for indx in range(len(arr)-8, len(arr)):
				flat.append(arr[indx])
		out = np.array([flat])
		return out

	# convert range of prediction 
	# -------------------------------------------------------------------------
	def transform(weight, frame):
		mn, mx = Account.lev_range[frame]
		
		OldRange = (1.0 - 0.4)
		NewRange = (mx - mn)
		NewValue = (((weight - 0.4) * NewRange) / OldRange) + mn

		return NewValue[0][0]

	# place an order for given pair
	# -------------------------------------------------------------------------
	def buy(units, pair, frame, close, lev, rg):
	
		# look at relative lows
		last_price = close[-1]
		min_price = 0
		l = len(close)

		# find low point for stop loss
		for lookBack in range(1, rg):
			if min_price > close[l-lookBack]:
				min_price = close[l-lookBack]

		STOP_LOSS = 0
		# for now, determine stop based on frame
		if frame == "H1":                #D
			STOP_LOSS = max((last_price*.99), min_price)
		elif frame == "H4":				 #H4
			STOP_LOSS = max((last_price*.985), min_price)

		# call order function from main module
		Trade.stop_loss_trade(Account, units, pair, STOP_LOSS, frame, last_price, rg)

	# determine if we should place an order on a waiting pair
	# -------------------------------------------------------------------------
	def buy_sig(weight, op, high, low, close, lev, pair, frame, rg):
		orders = 0

		if frame=="H4":
			rsi_level = 55
		else:
			rsi_level = 55

		fastk, fastd = StochRSI(close)
		if ((fastk[-1] >= fastd[-1]) and (fastk[-1] < rsi_level and close[-1])):

			if Trade.can_trade(Account, pair, frame):
				Balance = Account.getBalance()
				
				# we are ready to make a trade
				if Balance > 0:
					orders = 1

					# see if there was a bullish candle present
					candle = False
					hammer, engulf, pierce = bullish_candles(op, high, low, close)
					if hammer[-1] > 0 or engulf[-1] > 0 or pierce[-1] > 0:
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
					buy(units, pair, frame, close, lev, rg)
		
		return orders

	# determine if we should close a position
	# -------------------------------------------------------------------------
	def close_sig(op, high, low, close, pair, frame, ID, rg, age):

		day = datetime.datetime.today().weekday()
		age_acc = 0
		# differentiate between backtest and real program
		if Account == Trade:
			age_acc = 1
		elif day <= 4:
			if frame == "H1":
				age_acc = (1.0/4)
			elif frame == "H4":
				age_acc = (1.0/16)

		Account.set_age(ID, age_acc)

		# let trade develop
		if age < (rg - 20):
			return 0

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

		if frame == "H1":
			pred_data = Account.H1_SELL_scaler.transform(pred_data)
			prediction = Account.H1_SELL_model.predict(pred_data)

		elif frame == "H4":
			pred_data = Account.H4_SELL_scaler.transform(pred_data)
			prediction = Account.H4_SELL_model.predict(pred_data)

		if prediction < Account.prediction[ID]: # track min prediction
			Account.prediction[ID] = prediction

		logger.info("   < peak prediction for %s: %s", pair, str(Account.prediction[ID]))
		logger.info("   < alma: %s -- stochastic: %s for %s", str(aF[-1]-aS[-1]), str(stF[-1]-stS[-1]), pair)
		if Account.prediction[ID] < 0.35 and (aF[-1] < aS[-1]*1.001 and stF[-1] <= stS[-1]):
			closed = close_pos(ID, pair, frame, close)
		return 1

	# close a position for given pair
	# -------------------------------------------------------------------------
	def close_pos(ID, pair, frame, close):
		success = Trade.close_position(Account, ID, pair, frame, close[-1])
		closed = 1

		if success == False:
			print("< closing position failed, trying again")
			
			buffer_time = 10       
			time.sleep(buffer_time) # wait 10 seconds
			close_pos(ID, pair, frame, close)  # make recursive call to close position

		return closed

	# -------------------------------------------------------------------------
	# see if we need to close any positions
	# -------------------------------------------------------------------------
	closed = 0
	positions = Account.openPositions()
	vol = []
	close = []

	for ID in list(positions):
		pair, frame, rg, age = positions[ID]
		
		time, vol, op, high, low, close = Account.get_data(frame, pair)
		if vol.size == 0:
			continue
	
		closed += close_sig(op, high, low, close, pair, frame, ID, rg, age)

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
		weight = waiting[key_str][3]
		rg = waiting[key_str][4]
		lev = waiting[key_str][5]

		day = datetime.datetime.today().weekday()
		age_acc = 0
		# we want to add to waiting age but backtest 
		#    and forex_trading pull data differently
		if Account == Trade:
			age_acc = 1
			day = 0
		
		elif day <= 4:
			if frame == "H1":
				age_acc = (1.0/2.0)
			elif frame == "H4":
				age_acc = (1.0/8.0)
		
		if age < 3:
			Account.waiting[key_str][0] += age_acc # add to age
		
			time, vol, op, high, low, close = Account.get_data(frame, pair)

			if vol.size == 0:
				continue

			orders += buy_sig(weight, op, high, low, close, lev, pair, frame, rg)
		else:
			Account.end_waiting(key_str)



