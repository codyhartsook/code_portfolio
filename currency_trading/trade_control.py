#!/usr/bin/python

# main program:
# contains account and trade information
# -----------------------------------------------------------------------------
import warnings
import os
warnings.filterwarnings("ignore")

import oandapyV20
import pickle
import datetime
import logging
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
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# start the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('ledger.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(levelname)s - %(message)s')
fh.setFormatter(formatter)

logger.addHandler(fh)

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
		# H1 models and scalers
		self.H1_BR_model = load_model('H1_DNN_Breakout')
		self.H1_SELL_model = load_model('H1_SELL_OPT')
		self.H1_BR_scaler = joblib.load('H1_BR_scaler.save')
		self.H1_SELL_scaler = joblib.load('H1_SELL_scaler.save')
		# H4 models and scalers
		self.H4_BR_model = load_model('H4_DNN_Breakout')
		self.H4_SELL_model = load_model('H4_SELL_OPT')
		self.H4_BR_scaler = joblib.load('H4_BR_scaler.save')
		self.H4_SELL_scaler = joblib.load('H4_SELL_scaler.save')

		# frequency of data polling: number of times per 24 hourse
		self.data_poll = 48 # twice per hour

		# define leverage ranges
		self.lev_range = {}
		self.lev_range["H4"] = .04, .065
		self.lev_range["H1"] = .03, .055
		self.lev_boost = 0.06
		self.avg_lev = 0

		# account status information
		self.balance = 0
		self.trade_count = 0
		self.age = {}                   # pickle age
		self.waiting = {}				# pickle waiting
		self.last_transaction_ID = ''	# pickle las_transaction
		self.open_positions = {}		# pickle open_positions
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
			logger.error("V20Error: %s", e)
			#raise Exception("could not sync trades to api information")

	# upload oanda open positions to local memory
	# -------------------------------------------------------------------------
	def syncTrades(self):
		# load our pickled data structures
		self.load_data_structures()
		logger.info("   < local open positions:", self.open_positions)
		
		r = positions.OpenPositions(accountID=self.accountID)

		try:
			info = {}
			info = self.client.request(r)
			#print(info)

			# if there are not open positins on oanda
			if len(info['positions']) == 0:
				self.open_positions = {}

			for pos in info['positions']:

				trade_ids = pos['long']['tradeIDs']
				for ID in trade_ids:
					if ID not in self.open_positions:
						
						logger.warning("   < ID not in local positions: %s", str(ID))
						logger.warning("   < Error: need to update open_positions")
						
						# read from backup
						self.read_from_backup(ID)

				# sync age dict, this is necesary if trades are closed manually
				to_del1 = []
				to_del2 = []
				for ID_1, ID_2 in zip(self.age, self.open_positions):
					if ID_1 not in pos['long']['tradeIDs']:
						to_del1.append(ID_1)
					if ID_2 not in pos['long']['tradeIDs']:
						to_del2.append(ID_2)
				
				for ID in to_del1:
					del self.age[ID]
				for ID in to_del2:
					del self.open_positions[ID]

			# clear backup file
			open('backup_trades.txt', 'w').close()
					
		except V20Error as e:
			logger.error("V20Error: %s", e)
			raise Exception("could not sync trades to api information")

	# read the trade information we wrote to file to update program memory
	# -------------------------------------------------------------------------
	def read_from_backup(self, ID):
		
		#try:
		lines = [line.rstrip('\n') for line in open('backup_trades.txt')]
		for line in lines:
			data = line.split(',')

			#print(data, "<-data")

			ID = data[0].strip()
			pair = data[1].strip()
			frame = data[2].strip()
			rg = int(data[3].strip())

			self.addPosition(ID, pair, frame, rg)
		#except FileNotFoundError as f:
		#	print("no backup present")


	# add a position to our local memory
	# -------------------------------------------------------------------------
	def addPosition(self, ID, pair, frame, rg):
		self.open_positions[ID] = pair, frame, rg
		self.last_transaction_ID = ID
		self.age[ID] = 0

	# laod pickled objects
	# -------------------------------------------------------------------------
	def get_obj(self, name):
		#try:
		infile = open(name+'.pickle', 'rb')
		obj = pickle.load(infile)
		infile.close()
		return obj
		#except FileNotFoundError as f:
		#	return None

	def load_data_structures(self):
		self.get_obj("age")
		self.age = self.get_obj("age")
		self.waiting = self.get_obj("waiting")
		self.last_transaction_ID = self.get_obj("last_ID")
		self.open_positions = self.get_obj("open_positions")

    # save all local data structures to be used on on the next program instance
	# -------------------------------------------------------------------------
	def save(self):
		self.pickle_obj(self.age, "age")
		self.pickle_obj(self.waiting, "waiting")
		self.pickle_obj(self.last_transaction_ID, "last_ID")
		self.pickle_obj(self.open_positions, "open_positions")

	def pickle_obj(self, structure, name):
		outfile = open(name+'.pickle', 'wb')
		pickle.dump(structure, outfile)
		outfile.close()

	# retrieve the open positions we hold
	# -------------------------------------------------------------------------
	def openPositions(self):
		return self.open_positions

	# add currency pair and frame to list of possible trades to monitor
	# -------------------------------------------------------------------------
	def possible_trade(self, pair, frame, prediction, rg, o_slope, p_slope, obv, cycle, lev):
		waiting_str = pair+","+frame
		logger.info("adding %s to possible trades", waiting_str)
		self.waiting[waiting_str] = [0, pair, frame, 0, prediction, rg, lev]

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
		return float(self.balance)

	# retrieve candle data with api request
	# -------------------------------------------------------------------------
	def get_data(self, frame, pair):
		params = {
	        "count": 60,          # number of candles: 60 is default 
	        "granularity": frame}  # time frame

		try:
			r = instruments.InstrumentsCandles(instrument=pair, params=params)
			self.client.request(r) # request data
			time, vol, op, high, low, close = build_df(r)
			return time, vol, op, high, low, close
		except:
			logger.error("   < Error: trade_control/get_data -- could not retrive data")
			raise Exception("could not retrive data")

	def write_sell_pred(self, ID, prediction):
		pass

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
			open_pair, open_frame, rg = positions[ID]
			
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
		with open('/home/ec2-user/Trade/backup_trades.txt', 'r+') as backup:
			ln = str(ID)+", "+pair+", "+frame+", "+str(rg)+"\n"
			backup.write(ln)
			backup.close()

	# for testing
	def write_age(self):
		with open('/home/ec2-user/Trade/age_log.txt', 'r+') as writer:
			for ID in self.age:
				ln = (str(ID)+" -> "+str(self.age[ID])+"\n")
				writer.write(ln)
			writer.close()

	# write to trade log ledger
	# -------------------------------------------------------------------------
	def trade_log(self, ID, action, time, pair, frame):
		with open('/home/ec2-user/Trade/trade_log.txt', 'r+') as ledger:
			ln = "Trade: ID="+str(ID)+" | "+action+" | "+time+" | pair="+pair+" | stop_price="+str(stop_price)+"\n"
			logger.info("placing trade: %s", ln)
			ledger.write(ln)
			ledger.close()

	# initialize a stop loss trade 
	# -------------------------------------------------------------------------
	def stop_loss_trade(self, Account, units, pair, stop_price, frame, last_price, rg, sig_type):
		
		#if sig_type == 0: # short 
		#	units = (units * -1)
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
			Account.addPosition(res['orderFillTransaction']['id'], 
				res['orderFillTransaction']['instrument'], frame, rg)
			
			# write trade to backup file
			self.write_to_backup(res['orderFillTransaction']['id'], 
				res['orderFillTransaction']['instrument'], frame, rg)

			action = "Buy_Order"
			time = datetime.datetime.now()
			# write trade to trade log file
			self.trade_log(res['orderFillTransaction']['id'], action, time, pair, frame)

		except oandapyV20.exceptions.V20Error as err:
			logger.warning(err)
			raise Exception("erorr detected on order request")

	# close the position for the given ID
	# -------------------------------------------------------------------------
	def close_position(self, Account, ID, pair, frame, close, pos_type):
		logger.info("   < closing a position for ID =", ID, ">\n")
		r = orders.OrderCancel(accountID=Account.accountID, orderID=ID)
		try:
			Account.client.request(r)
			del Account.open_positions[ID] # remove from local dict
			del Account.age[ID]

			action = "Sell_Order"
			time = datetime.datetime.now()
			self.trade_log(ID, action, time, pair, frame)

			return True
		except:
			raise Exception("could not close position")

# -----------------------------------------------------------------------------
# program execution starts
# look for buy and selling signals then sleep 
# -----------------------------------------------------------------------------
if __name__ == "__main__":

	#print("/////////////////////////////////////////////////////////////////////////")
	#logger.info('// initializing forex program')
	logger.info('-- timestamp: %s', str(datetime.datetime.now()))
	#print("/////////////////////////////////////////////////////////////////////////\n")

	ACCOUNT = Account() # get an instance of the Account class
	TRADE = Trade()     # get an instance of the Trade class

	try:
		for frame in ["H4", "H1"]:
			
			# run sub-program to find buying signals
			find_signal(ACCOUNT, TRADE, frame)

		# run sub-program to find selling signals
		manage_position(ACCOUNT, TRADE)

		ACCOUNT.save()
		ACCOUNT.load_data_structures()

		# program summary
		logger.info("   < acount balance: %s", str(ACCOUNT.getBalance()))
		logger.info("   < trade count: %s", str(ACCOUNT.trade_count))
		logger.info("   < number of IDs in waiting: %s", str(len(ACCOUNT.waiting)))
		logger.info("   < number of IDs in age: %s", str(len(ACCOUNT.age)))

	except Exception as err:
		print(err)
		logger.error("Error occured in main program: %s", err)
		logger.error("\n<Usage>: exiting program")
		exit()











