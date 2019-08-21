# Decentralized Cloud Computing

This is a proof of concept for a decentralized cloud computing  
infrustructure. The purpose of this project is to observe and  
study how a system of this type could operate and is not designed     
for commercial use.  

## Description

As cloud computing becomes more prevalent, the energy impact of the  
underlying infrastructure has risen greatly. This project aims to  
rethink cloud computing design, providing an architecture prototype.    
The goal of this architecture is to provide a cloud computing service     
while minimizing the electricity impact and cost associated with  
performing a computational task. This is accomplished by providing a  
dynamic network of small servers distributed throughout the operating  
region. As electricity production and demand varies daily and season -     
ally, the network can dynamically match clients to servers in lower  
demand regions. In theory, this will help balance the power grid and   
take advantage of electricity price differences.  

## Design

The system consists of a central network server, distributed compute  
engine servers, and clients. The network server will store a reference to      
compute servers in a K-dimensional tree for efficient locality searching.  
When clients want to use the system they connect to the central server  
which then routes them to a compute server. All further action is peer  
to peer between the client and the compute server.  

When a client connects to the network, they are connected to the  
compute server with minimum weighted distance from them. This distance  
is defined as the distance between two, three-dimensional points in space.    
The x and y coordinates represent longitude and latitude while the z   
coordinate is a function of local energy cost and demand. The matching is  
done by searching the network server's 3-dimensional tree of compute  
servers which returns the server with the smallest distance to the client.  
A critical aspect of the system is defining the z coordinate of the  
compute servers. This will be done by retrieving the real-time electricity  
cost in the region of the server and using that to generate a discrete   
value. This value must be large enough that it can out-weigh the x and y  
coordinates when computing the closest neighbor. This will enable clients  
to connect to servers in low cost/low demand regions.  

