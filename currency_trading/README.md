Synopsis
----------------------------------------------------------------------------
python3 trade_control.py  
python3 back_test.py --frame [H1, H4, D]

Requirements
----------------------------------------------------------------------------
python3  
numpy  
pandas  
talib (python wrapper for talib)  
oandaV20  

Description
----------------------------------------------------------------------------
**trade_control.py** is a terminal based automated currency trading application  
being run on an aws ec2 instance.  
**back_test.py** is the associated backtesting program.  

Forex data and orders are issued through an oanda forex account.  
  
trade_control.py pulls real time forex data for all major currency    
pairs on three different chart times. Price and volume technical analysis  
indicators are generated using the api data in order to find divergences between   
price and volume. This data is then passed to two trainded deep neural networks 
which predict a price breakout for the given currency. If the prediction  
confidence is above a threshold, the currency pair on the given chart time will  
be added to a set of possible trades. If additional signals are met, the program  
will place a stop loss order for the currency pair. Account positions are then  
monitored in order to find the optimal time in which to close a position. This  
process is aided by two additional deep neural network to predict the optimal  
close point.

back_test.py pulls historical data for all currency pairs on three different   
chart times. The program's internal class then provides the client programs  
with sliding intervals of data to replicate running on real time data. If a   
signal is found in the historical data, the backtesting program will mimic   
the functionality of the oanda brokerage in order to keep track of account  
information.

Disclosure
-----------------------------------------------------------------------------
The program can place real orders and close account positions, although it  
is still under development and has only been linked to a practice trading  
account. The trading success of the application is untested and it should  
not be used with a live account.  

The backtesting program has shown that significant returns are possible.
