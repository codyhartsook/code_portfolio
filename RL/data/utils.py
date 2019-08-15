# utility and technical analysis functinons for the forex_2.0 program

import pandas as pd
import talib as ta
import numpy as np

# anoud legoux moving average, inner and outer functions
# -----------------------------------------------------------------------------
def ALMA(Price):
	Window = 6
	Sigma = 3
	almaF = alma(Price, Window, Sigma)

	Window = 20
	Sigma = 12
	almaS = alma(Price, Window, Sigma)

	return almaF, almaS

def alma(data, period, s) :
        
        m = np.floor(0.85 * (period - 1))
        alma = np.zeros(data.shape)
        w_sum = np.zeros(data.shape)

        for i in range(len(data)):
            if i < period - 1:
                continue
            else:
                for j in range(period):
                    w = np.exp(-(j-m)*(j-m)/(2*s*s))
                    alma[i] += data[i - period + j] * w
                    w_sum[i] += w
                alma[i] = alma[i] / w_sum[i]

        return alma

# RSI
def RSI(df):
	data = df['Close'].as_matrix()
	rsi = ta.RSI(data, timeperiod=14)
	return rsi

# Haiken candles
def HA(df):
    df['HA_Close']=(df['Open']+ df['High']+ df['Low']+df['Close'])/4

    idx = df.index.name
    df.reset_index(inplace=True)

    for i in range(0, len(df)):
        if i == 0:
            df.set_value(i, 'HA_Open', ((df.get_value(i, 'Open') + df.get_value(i, 'Close')) / 2))
        else:
            df.set_value(i, 'HA_Open', ((df.get_value(i - 1, 'HA_Open') + df.get_value(i - 1, 'HA_Close')) / 2))

    if idx:
        df.set_index(idx, inplace=True)

    df['HA_High']=df[['HA_Open','HA_Close','High']].max(axis=1)
    df['HA_Low']=df[['HA_Open','HA_Close','Low']].min(axis=1)
    return df

# stochastic of rsi
# -----------------------------------------------------------------------------
def StochRSI(data):
	fastk, fastd = ta.STOCHRSI(data, timeperiod=14, fastk_period=5, 
		fastd_period=3, fastd_matype=0)
	return fastk, fastd

# helper function: computes the running mean or moving average
# -----------------------------------------------------------------------------
def running_mean(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

# normalized average true range
def NATR(df):
	high = df['High'].as_matrix()
	low = df['Low'].as_matrix()
	close = df['Close'].as_matrix()
	
	real = ta.NATR(high, low, close, timeperiod=20)
	return real

def chaikin_mf(high, low, close, volume):
	df["MF Multiplier"] = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"]))/(df["High"] - df["Low"])
	df["MF Volume"] = df["MF Multiplier"] * df["Volume"] 
	CMF_for_period = df["MF Volume"].sum()/df["Volume"].sum()

def MACD(close):
	macd, macdsignal, macdhist = ta.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
	return macd, macdsignal, macdhist

# on balance volume
# -----------------------------------------------------------------------------
def OBV(df):
	close = df['Close'].as_matrix()
	vol = df['Volume'].as_matrix()
	obv = ta.OBV(close, vol)
	return obv

# candlestick patterns:
# bullish: hammer, engulfing, pearcing line, tree white soldiers
# bearish: evening star, hanging man, bearish engulfing
def bullish_candles(op, high, low, close):
	hammer = ta.CDLHAMMER(op, high, low, close) # hammer
	engulf = ta.CDLENGULFING(op, high, low, close) # engulfing
	pierce = ta.CDLPIERCING(op, high, low, close) # peircing line
	
	return hammer, engulf, pierce

def bearish_candles(op, high, low, close):
	star = ta.CDLEVENINGSTAR(op, high, low, close, penetration=0)
	hanging = ta.CDLHANGINGMAN(op, high, low, close)
	engulf = engulf = ta.CDLENGULFING(op, high, low, close) # engulfing
	belt = ta.CDLBELTHOLD(op, high, low, close)

	return star, hanging, engulf, belt

# build data frame from json object
# -----------------------------------------------------------------------------
def build_df(r):
	# order data into dataframe
	r.response['candles'][0]['mid']
	r.response['candles'][0]['time']
	r.response['candles'][0]['volume']
	
	dat = []
	for oo in r.response['candles']:
	   	dat.append([oo['time'], oo['volume'], oo['mid']['o'], 
	   		oo['mid']['h'], oo['mid']['l'], oo['mid']['c']])

	df = pd.DataFrame(dat)
	df.columns = ['Time', 'Volume', 'Open', 'High', 'Low', 'Close']

	open_data = df.as_matrix(columns=[df.columns[2]])
	open_new_shape = np.reshape(open_data, (-1, 1))  # reshape the array
	open_data = open_new_shape.flatten()
	open_data = open_data.astype(float)

	high_data = df.as_matrix(columns=[df.columns[3]])
	high_new_shape = np.reshape(high_data, (-1, 1))  # reshape the array
	high_data = high_new_shape.flatten()
	high_data = high_data.astype(float)

	low_data = df.as_matrix(columns=[df.columns[4]])
	low_new_shape = np.reshape(low_data, (-1, 1))  # reshape the array
	low_data = low_new_shape.flatten()
	low_data = low_data.astype(float)

	close_data = df.as_matrix(columns=[df.columns[5]])
	close_new_shape = np.reshape(close_data, (-1, 1))  # reshape the array
	close_data = close_new_shape.flatten()
	close_data = close_data.astype(float)

	vol_data = df.as_matrix(columns=[df.columns[1]])
	vol_new_shape = np.reshape(vol_data, (-1, 1))   # reshape the array
	vol_data = vol_new_shape.flatten()
	vol_data = vol_data.astype(float)

	time_data = df.as_matrix(columns=[df.columns[0]])
	t_new_shape = np.reshape(time_data, (-1, 1))   # reshape the array
	time_data = t_new_shape.flatten()

	df['Time'] = time_data
	df['Volume'] = vol_data
	df['Open'] = open_data
	df['High'] = high_data
	df['Low'] = low_data
	df['Close'] = close_data
	
	return df

