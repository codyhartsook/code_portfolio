# Decentralized Cloud Computing

This is a proof of concept for a decentralized cloud computing network.  
The purpose of this project is to observe and study how a network of  
this type might work and is not intended for commercial use. 

## Description
The aim of this project is to provide a cloud computing service while  
minimizing the electricity impact and cost associated with performing  
a computational task. This will be done by providing a dynamic network  
of small servers distributed throughout the operating region. As  
electricity production and demand vary throughout the day, the network  
can offload tasks to lower demand regions. In theory this will help  
balance the power grid and take advantage of price differences.  

## Design

The system consists of a central server, compute servers, and clients.  
Compute servers establish a connection to the central server which in  
turn stores their IP and location. When clients want to use the system  
they connect to the central server which then directs them to a compute  
server. All further action is peer to peer between the client and the  
compute server.  

When a client connects to the network, they are connected to the  
compute server with minimun weighted distance from them. This distance  
is defined as the Euclidean distance minus an energy bias. This is  
accomplished using the closest pair of points algorithm but where  
points are defined as discs. The center of each disc is the location of   
the server and the radius is a function of the local electricity cost.  
The lower the regional cost, the larger the radius. The network then  
tries to find the closest disc to the end user's location.  
