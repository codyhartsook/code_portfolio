#!/usr/bin/python
# sub program to close account positions

import time
from utility_funcs import StochRSI, bullish_candles, bearish_candles, ALMA, RSI, MACD


def manage_position(Account, Trade):

	# place an order for given pair
	# -------------------------------------------------------------------------
	def buy(units, pair, close, frame):
	
		# look at relative lows
		last_price = close[-1]
		min_price = 0
		l = len(close)

		# find low point for stop loss
		for lookBack in range(1, 30):
			if min_price > close[l-lookBack]:
				min_price = close[l-lookBack]

		STOP_LOSS = 0
		# for now, determine stop based on frame
		if frame == "H1":                #D
			STOP_LOSS = max((last_price*.992), min_price)
		elif frame == "H4":				 #H4
			STOP_LOSS = max((last_price*.99), min_price)
		elif frame == "D":			 #H1
			STOP_LOSS = max((last_price*.98), min_price)

		# call order function from main module
		Trade.stop_loss_trade(Account, units, pair, STOP_LOSS, frame, last_price)

	# determine if we should place an order on a waiting pair
	# -------------------------------------------------------------------------
	def buy_sig(op, high, low, close, lev, frame, pair, key_str):
		orders = 0

		if frame=="H4":
			rsi_level = 55
		else:
			rsi_level = 55

		fastk, fastd = StochRSI(close)
		if (fastk[-1] >= fastd[-1]) and (fastk[-1] < rsi_level and close[-1]):

			if Trade.can_trade(Account, pair, frame):
				Balance = Account.getBalance()
				if Balance > 0:
					orders = 1

					candle = False
					hammer, engulf, pierce = bullish_candles(op, high, low, close)
					if hammer[-1] > 0 or engulf[-1] > 0 or pierce[-1] > 0:
						candle = True

					# if we found reversal candle, increase leverage slightly
					if candle:
						trade_value = (Balance*Account.lev_boost*50)
					else:
						trade_value = (Balance*Account.leverage[frame])*50

					units = trade_value/close[-1]

					buy(units, pair, close, frame)
		
		return orders

	# determine if we should close a position
	# -------------------------------------------------------------------------
	def close_sig(op, high, low, close, pair, frame, ID):
		if Account.age[ID] < 5:
			
			# differentiate between backtest and real program
			if Account == Trade:
				age_acc = 1
			else:
				if frame == "H1":
					age_acc = (1.0/4)
				elif frame == "H4":
					age_acc = (1.0/16)
				elif frame == "D":
					age_acc = (1.0/96)

			Account.age[ID] += age_acc
			return 0

		almaF, almaS = ALMA(close)
		fastk, fastd = StochRSI(close)

		if almaF[-1] < almaS[-1] and fastk[-1] < fastd[-1]:
			closed = close_pos(ID, close)
		return 1

	# close a position for given pair
	# -------------------------------------------------------------------------
	def close_pos(ID, close):
		success = Trade.close_position(Account, ID, close[-1])
		closed = 1

		if success == False:
			print("< closing position failed, trying again")
			
			buffer_time = 10       
			time.sleep(buffer_time) # wait 10 seconds
			close_pos(ID)  # make recursive call to close position

		return closed

	# -------------------------------------------------------------------------
	# see if we need to close any positions
	# -------------------------------------------------------------------------
	
	# evaluate positions held
	closed = 0
	positions = Account.openPositions()
	vol = []
	close = []

	for ID in list(positions):
		pair, frame = positions[ID]
		
		time, vol, op, high, low, close = Account.get_data(frame, pair)
		if vol.size == 0:
			continue
	
		closed += close_sig(op, high, low, close, pair, frame, ID)

	# -------------------------------------------------------------------------
	# see if there was a trigger hit
	# -------------------------------------------------------------------------
	orders = 0
	waiting = Account.Waiting()
	
	for key_str in list(waiting):

		age = waiting[key_str][0]
		pair = waiting[key_str][1]
		frame = waiting[key_str][2]
		lev = waiting[key_str][3]

		# we want to add to waiting age but backtest 
		#    and forex_trading pull data differently
		if Account == Trade:
			age_acc = 1
		else:
			if frame == "H1":
				age_acc = (1.0/4)
			elif frame == "H4":
				age_acc = (1.0/16)
			elif frame == "D":
				age_acc = (1.0/96)
		
		if age < 3:
			Account.waiting[key_str][0] += age_acc # add to age
		
			time, vol, op, high, low, close = Account.get_data(frame, pair)

			if vol.size == 0:
				continue

			orders += buy_sig(op, high, low, close, lev, frame, pair, key_str)
		else:
			Account.end_waiting(key_str)








