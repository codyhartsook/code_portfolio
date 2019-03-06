# Synopsis
This project consists of four deep neural networks trained on data gathered  
by my backtesting program for currency trading as well as some similar  
data generation programs. The breakout models try to predict a price breakout  
for a given currency on the hourly chart time and the four hour chart time.  
Since the data differs for the two chart times, a different model is used for  
each. The peak prediction models try to predict the certainty of the current  
state. This is defined as being on the positve slope side prior to a peak or  
the negative slope side after a peak. 

The breakout models can be seen as a trend reversal indicator while the peak  
prediction models are used for position management.

# Model structure
The deep neural nets consist of an input layer, output layer, and five  
hidden layers. The hidden layers use the ReLU activation function while  
the output layer uses a sigmoid activation to output the probability  
of classification. The models is trained on 50 - 150 epochs as the test loss  
and accuracy seems to tail off at that point. 

# Results
The models have posted train accuracies between 0.92 - .96 and a test accuracy  
of 0.9 - 0.94. 
