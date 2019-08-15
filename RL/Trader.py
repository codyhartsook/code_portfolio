# trading class
import numpy as np

# very simplistic class to compute profit and label input data with opt output
class Trade():

	def __init__(self):
		self.open_position = -1
		self.state = -1 # 1=long, 2=short, 3=hold/nothing, 4=close_out
		self.opt_seq = []
		self.reward = 0

	def place_trade(self, trade_type, last_price):

		if trade_type == 0: # go long
			if self.state != 0:
				self.open_position = last_price
				self.state = 0
			return 0

		elif trade_type == 1: # go short
			if self.state != 1:
				self.open_position = last_price
				self.state = 1
			return 0

		elif trade_type == 4: # close out
			profit = 0

			if self.state == 0:
				profit = (last_price - self.open_position)

			elif self.state == 1:
				profit = (self.open_position - last_price)
			
			self.state = -1
			self.open_position = 0
			return profit

		else:
			return 0
			

	# this is the foundation of our system, it defines what our goal is
	# we get to see the future market and pick the optimal strategy 
	# opt strategy will be returned as a sequence of buy, hold, sell signals
	def opt_event_timeline(self, candles):

		if candles.size == 0:
			self.opt_seq = [3] * len(candles)
			return self.opt_seq

		max_index = np.argmax(candles)
		min_index = np.argmin(candles)
		swing = self.swing(candles)
	
		volatility = (swing > 0.075) # important value, should be tuned
		self.opt_seq = []

		# setup for long trade
		# fill in opt sequence
		if max_index > min_index and volatility:
			for index in range(0, len(candles)):
				if index == min_index:
					self.opt_seq.append(1)
				elif index == max_index:
					self.opt_seq.append(4)
				else:
					self.opt_seq.append(3)

		# setup for short trade
		# fill in opt sequence
		elif min_index > max_index and volatility:
			for index in range(0, len(candles)):
				if index == max_index:
					self.opt_seq.append(2)
				elif index == min_index:
					self.opt_seq.append(4)
				else:
					self.opt_seq.append(3)

		# not volatile enough
		# fill in opt sequence
		else:
			self.opt_seq = [3] * len(candles) # do nothing the entire time

		if len(self.opt_seq) != len(candles):
			raise Exception ("len of opt does not match candles")

		return self.opt_seq

	def swing(self, close):
		MAX = max(close)
		MIN = min(close)

		diff = MAX - MIN
		delta = ((diff / MIN) * 100)

		return delta

if __name__ == "__main__":
	TR = Trade()

	TR.place_trade(1, 6)
	TR.place_trade(1, -3)
	TR.place_trade(1, 2)
	TR.place_trade(1, 4)
	reward = TR.place_trade(4, 3)

	print("profit:", reward)
	










