Synopsis
-----------------------------------------------------------------------------
**remove/server**: ./cixd  
**local/client**: ./cix  

Description
-----------------------------------------------------------------------------
This folder contains code for a multithreaded client/server application.   
Client and server programs are connected via sockets on a desired port. A    
protocol is also provided to define the communication between the programs.  
Once a connection between the client and server is made, the server program  
forks a child process to respond to the client while the parent process   
remains ready to respond to additional clients. After the client disconnects,   
the parent process kills the child process.

**client commands**:   

help &nbsp;- print help string  
exit &nbsp; - exit program  
ls &nbsp; &nbsp; &nbsp;- print contents of remote server  
get &nbsp; - get contents of remote server  
put &nbsp; - put a file on the remote server  
rm &nbsp; &nbsp;- rm a file from the remote server 
