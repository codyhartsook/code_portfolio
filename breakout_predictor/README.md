# Synopsis
Project consists of a deep neural net that is trained on data gathered  
by my backtesting program for currency trading. The model predicts  
whether a given currency will breakout of it's current low and therefore  
can be used as a trend reversal indicator. The prediction is treated as  
a binary classification problem where a class of 0 indicates the  
currency did not breakout, and a class of 1 indicates a breakout.

# Model structure
The deep neural net conssists of an input layer, output layer, and five  
hidden layers. The hidden layers use the ReLU activation function while  
the output layer uses a sigmoid activation to output the probablility  
of classification. The model is trained on 150 epochs as the test loss  
and accuracy seems to tail off at that point. 

# Results
The model currently has a train accuracy of .90 - .94 and a test accuracy  
of .85 - .88, indicating slight overfitting. 
