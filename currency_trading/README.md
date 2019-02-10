Synopsis
----------------------------------------------------------------------------
python3 trade_control.py  
python3 back_test.py --frame [H1, H4, D]

Requirements
----------------------------------------------------------------------------
python3  
numpy  
talib (python wrapper for talib)  
oandaV20  

Description
----------------------------------------------------------------------------
**trade_control.py** is a terminal based automated currency trading application.  
**back_test.py** is the associated backtesting program.  

Forex data and orders are issued through an oanda forex account.  
  
trade_control.py repeatedly pulls real time forex data for all major currency    
pairs on three different chart times. Price and volume technical analysis  
indicators are generated using the api data in order to find divergences between   
price and volume. If a divergence is found, in addition to a stochastic bullish   
crossover, the program will place a stop loss order for the currency pair.    
Account positions are then monitored in order to find the optimal time in  
which to close a position.  

back_test.py pulls historical data for all currency pairs on three different   
chart times. The program's internal class then provides the client programs  
with sliding intervals of data to replicate running on real time data. If a   
signal is found in the historical data, the back testing program will mimic   
the functionality of the oanda brokerage in order to keep track of account  
information.

Disclosure
-----------------------------------------------------------------------------
The program can place real orders and close account positions, although it  
is still under development and has only been linked to a practice trading  
account. The trading success of the application is untested and it should  
not be used with a live account.  

The backtesting program has posted varied results. Backtests on the H4 and D  
charts have posted significant positive returns while H1 backtests have posted  
small losses.  

Future plans
--------
* In the process of deploying the application to an AWS EC2 server to be run  
continuously on the cloud.

* Developing a logistic regression model to optimize the trade entry point.  
Model data consists of technical price and volume signals taken from the  
the time of trade entry (data collected by the backtesting prgram). Additionally,      
a label has been added to indicate whether the trade was profitable or not.  
Using this data, I plan to train the logistic regression model and use it to  
help predict whether the proposed trade is likely to be profitable.
