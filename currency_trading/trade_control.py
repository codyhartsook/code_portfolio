#!/usr/bin/python

# main program:
# contains account and trade information
# -----------------------------------------------------------------------------
import warnings
warnings.filterwarnings("ignore")

import oandapyV20
from Authenticate import Auth
from find_signals import find_signal
from utility_funcs import build_df
from order_execution import manage_position
import oandapyV20.endpoints.instruments as instruments
import oandapyV20.endpoints.positions as positions
import oandapyV20.endpoints.accounts as accounts
import oandapyV20.endpoints.orders as orders
from oandapyV20.exceptions import V20Error
from oandapyV20.contrib.requests import (
    MarketOrderRequest,
    TakeProfitDetails,
    StopLossDetails)

# for ml predictions
from sklearn import preprocessing
from sklearn.externals import joblib
from keras.models import load_model

# -----------------------------------------------------------------------------
# class account
# store and update account information to be accessed by modules
# -----------------------------------------------------------------------------
class Account():
	def __init__(self):
		# oanda info
		self.accountID, self.access_token = Auth()
		self.client = oandapyV20.API(access_token=self.access_token)

		# load ml models and scalers to make predictions
		self.H4_BR_model = load_model('H4_DNN_Breakout')
		self.H1_BR_model = load_model('H1_DNN_Breakout')
		self.H4_SELL_model = load_model('H4_SELL_OPT')
		self.H1_SELL_model = load_model('H1_SELL_OPT')
		self.H4_BR_scaler = joblib.load('H4_BR_scaler.save')
		self.H1_BR_scaler = joblib.load('H1_BR_scaler.save')
		self.H4_SELL_scaler = joblib.load('H4_SELL_scaler.save')
		self.H1_SELL_scaler = joblib.load('H1_SELL_scaler.save')

		# define leverage ranges
		self.lev_range = {}
		self.lev_range["H4"] = .04, .065
		self.lev_range["H1"] = .03, .055
		self.lev_boost = 0.06
		self.avg_lev = 0

		# account status information
		self.balance = 0
		self.trade_count = 0
		self.age = {}
		self.waiting = {}
		self.last_transaction_ID = ''
		self.open_positions = {}
		self.max_trade_count = 20
		self.updateAccountInfo()
		self.syncTrades()

	# once program initializes, we want to retrieve account information
	# -------------------------------------------------------------------------
	def updateAccountInfo(self):
		# get information about oanda account
		r = accounts.AccountSummary(accountID=self.accountID)

		try:
			data = self.client.request(r)

			self.balance = data['account']['balance']
			self.trade_count = data['account']['openTradeCount']
			self.last_transaction_ID = data['account']['lastTransactionID']

		except V20Error as e:
			print("V20Error:", e)

	# upload oanda open positions to local memory
	# -------------------------------------------------------------------------
	def syncTrades(self):
		# get information about oanda account
		r = positions.OpenPositions(accountID=self.accountID)

		try:
			info = {}
			info = self.client.request(r)
			for pos in info['positions']:
				trade_ids = pos['long']['tradeIDs']
				for ID in trade_ids:
					if ID not in self.open_positions:
						# read from backup file then clear backup file
						print("updating open_positions")
						self.read_from_backup(ID)
			# clear backup file
			open('backup_trades', 'w').close()
					
		except V20Error as e:
			print("V20Error:", e)
			exit()

	# read the trade information we wrote to file to update program memory
	# -------------------------------------------------------------------------
	def read_from_backup(self, ID):
		try:
			lines = [line.rstrip('\n') for line in open('backup_trades')]
			for line in lines:
				data = line.split(',')
				ID = data[0]
				pair = data[1]
				frame = data[2]
				rg = data[3]

				self.addPosition(ID, pair, frame, rg)
		except FileNotFoundError as f:
			print("no backup present")

	# retrieve the open positions we hold
	# -------------------------------------------------------------------------
	def openPositions(self):
		return self.open_positions

	# add a position to our local memory
	# -------------------------------------------------------------------------
	def addPosition(self, ID, pair, frame, rg):
		self.open_positions[ID] = pair, frame, rg
		self.last_transaction_ID = ID
		self.age[ID] = 0

	# add currency pair and frame to list of possible trades to monitor
	# -------------------------------------------------------------------------
	def possible_trade(self, pair, frame, prediction, rg, o_slope, p_slope, obv, cycle, lev):
		waiting_str = pair+","+frame
		self.waiting[waiting_str] = [0, pair, frame, prediction, rg, lev]

	# retrieve a waiting currency pair/frame object
	# -------------------------------------------------------------------------
	def Waiting(self):
		return self.waiting

	# remove currency pair/frame from list
	# -------------------------------------------------------------------------
	def end_waiting(self, w_str):
		del self.waiting[w_str]

	# retrieve account balance
	# -------------------------------------------------------------------------
	def getBalance(self):
		self.updateAccountInfo()
		return float(self.balance)

	# retrieve candle data with api request
	# -------------------------------------------------------------------------
	def get_data(self, frame, pair):
		params = {
	        "count": 60,          # number of candles    
	        "granularity": frame}  # time frame

		try:
			r = instruments.InstrumentsCandles(instrument=pair, params=params)
			self.client.request(r) # request data
			time, vol, op, high, low, close = build_df(r)
			return time, vol, op, high, low, close
		except:
			print("Error: forex_trading.py/get_data() -- could not retrive data")
			print("will try again after buffer time")

			buffer_time = 10
			time.sleep(buffer_time)
			self.get_data(frame, pair)

# -----------------------------------------------------------------------------
# class Trade
# store and update trade information
# -----------------------------------------------------------------------------
class Trade():
	def __init__(self):
		self.positions = []

	# determine if we are already in this trade
	def can_trade(self, Account, pair, frame):
		Account.updateAccountInfo()
		
		trade_count = Account.trade_count
		if trade_count >= Account.max_trade_count:
			return False

		positions = Account.openPositions()
		for ID in positions:
			open_pair, open_frame = positions[ID]
			
			open_pair = open_pair.strip()
			open_frame = open_frame.strip()
			pair = pair.strip()
			frame = frame.strip()

			if open_pair == pair and open_frame == frame:
				return False
		return True

	# write to backup file in case of a program crash
	# -------------------------------------------------------------------------
	def write_to_backup(self, ID, pair, frame, rg):
		with open('backup_trades', 'a') as backup:
			ln = str(ID)+", "+pair+", "+frame+", "+str(rg)+"\n"
			backup.write(ln)
			backup.close()

	# write to trade log ledger
	# -------------------------------------------------------------------------
	def trade_log(self, ID, pair, frame, stop_price):
		with open('trade_log', 'a') as ledger:
			ln = "Trade: ID="+str(ID)+" | pair="+pair+" | stop_price="+str(stop_price)+"\n"
			ledger.write(ln)
			ledger.close()

	# initialize a stop loss trade 
	# -------------------------------------------------------------------------
	def stop_loss_trade(self, Account, units, pair, stop_price, frame, last_price, rg):
		
		# define the order request
		mktOrder = MarketOrderRequest(
    		instrument=pair,
    		units=units,
    		stopLossOnFill=StopLossDetails(price=stop_price).data
		)

		api = Account.client
		accountID = Account.accountID
		access_token = Account.access_token

		try:
    		# request the order
			r = orders.OrderCreate(accountID, data=mktOrder.data)
			api.request(r)
			res = r.response

			# add ID, pair, frame, range to open positions
			Account.addPosition(res['orderCreateTransaction']['id'], 
				res['orderCreateTransaction']['instrument'], frame, rg)
			
			#print("< order ID:", Account.last_transaction_ID)

			# write trade to backup file
			self.write_to_backup(res['orderCreateTransaction']['id'], 
				res['orderCreateTransaction']['instrument'], frame, rg)

			# write trade to trade log file
			self.trade_log(res['orderCreateTransaction']['id'], pair, frame, stop_price)

		except oandapyV20.exceptions.V20Error as err:
			print("erorr detected on order request")
			print(err)
			exit()

	# close the position for the given ID
	# -------------------------------------------------------------------------
	def close_position(self, Account, ID, close):
		print("< closing a position for ID =", ID, ">\n")
		r = orders.OrderCancel(accountID=Account.accountID, orderID=ID)
		try:
			Account.client.request(r)
			del Account.open_positions[ID] # remove from local dict
			del Account.age[ID]
			return True
		except:
			print("< position could not be closed")
			return False

# -----------------------------------------------------------------------------
# program execution starts
# look for buy and selling signals then sleep 
# -----------------------------------------------------------------------------
if __name__ == "__main__":

	ACCOUNT = Account() # get an instance of the Account class
	TRADE = Trade()     # get an instance of the Trade class

	print("/////////////////////////////////////////////////////////////////////////")
	print("// initializing forex program")
	print("/////////////////////////////////////////////////////////////////////////\n")

	#try:
		
	for frame in ["H4", "H1"]:
		
		# run sub-program to find buying signals
		find_signal(ACCOUNT, TRADE, frame)

	# run sub-program to find selling signals
	manage_position(ACCOUNT, TRADE)

	# program summary
	print("< acount balance:", ACCOUNT.getBalance())
	print("< trade count:", ACCOUNT.trade_count)

	#except:
	#	print("\n<error occured>: exiting program")
	#	exit()











