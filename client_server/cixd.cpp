// $Id: cixd.cpp,v 1.7 2016-05-09 16:01:56-07 - - $
// server daemon, moniters client requests and forks a child process   
//    if a client connects 

#include <iostream>
#include <string>
#include <vector>
#include <fstream> 
using namespace std;

#include <libgen.h>
#include <sys/types.h>
#include <unistd.h>

#include "protocol.h"
#include "logstream.h"
#include "sockets.h"

logstream log (cout);
struct cix_exit: public exception {};

// complete
void lsout (accepted_socket& client_sock, cix_header& header) {
   const char* ls_cmd = "ls -l 2>&1";
   FILE* ls_pipe = popen (ls_cmd, "r"); // open pipe
   if (ls_pipe == NULL) { 
      header.command = cix_command::NAK;
      header.nbytes = errno;
      send_packet (client_sock, &header, sizeof header);
      return;
   }
   string ls_output;
   char buffer[0x1000];
   for (;;) {
      char* rc = fgets (buffer, sizeof buffer, ls_pipe); 
      if (rc == nullptr) break;
      ls_output.append (buffer); // append to output
   }
   int status = pclose (ls_pipe); // close pipe
   
   header.command = cix_command::LSOUT;
   header.nbytes = ls_output.size();
   memset (header.filename, 0, FILENAME_SIZE);
   send_packet (client_sock, &header, sizeof header);
   send_packet (client_sock, ls_output.c_str(), ls_output.size());
}

void put_file(accepted_socket& client_sock, cix_header& header) {
   // write file into memory

   // create file with given name
   string file = header.filename;
   ofstream new_file;
   new_file.open (file);

   // get the file contents
   char buffer[header.nbytes]; // add one for null plug
   recv_packet (client_sock, buffer, header.nbytes);

   string str_file;
   for (unsigned int i=0; i<header.nbytes; ++i){
      str_file += buffer[i];
   }
   new_file << str_file;

   header.command = cix_command::ACK;
   send_packet (client_sock, &header, sizeof header);

}

void send_file(accepted_socket& client_sock, cix_header& header) {
   // read from memory then send to client
   string file = header.filename;
   ifstream is (file, ifstream::binary);
   if (is) {  
      // prepare to head file
      is.seekg (0, is.end);
      int length = is.tellg();
      is.seekg (0, is.beg);
      
      // read file
      char * buffer = new char [length];
      is.read (buffer,length);

      if (not is) {
         header.command = cix_command::NAK;
         header.nbytes = errno;
         send_packet (client_sock, &header, sizeof header);
         return;
      }
      is.close();

      // send buffer down socket
      header.nbytes = strlen(buffer);      
      header.command = cix_command::ACK;
      send_packet(client_sock, &header, sizeof header);
      send_packet(client_sock, buffer, header.nbytes);
   }
   else{
      header.command = cix_command::NAK;
      header.nbytes = errno;
      send_packet (client_sock, &header, sizeof header);
   }
}

void remove_file(accepted_socket& client_sock, cix_header& header) {
   // remove file from server memory
   string filename = header.filename;

   int success = unlink(filename.c_str());
   
   if( success < 0 ){
      header.command = cix_command::NAK;
      header.nbytes = errno;
      send_packet (client_sock, &header, sizeof header);
   }
   else {
      header.command = cix_command::ACK;
      send_packet(client_sock, &header, sizeof header);
   }
}


// incomplete
void run_server (accepted_socket& client_sock) {
   try {   
      for (;;) {
         cix_header header; 
         recv_packet (client_sock, &header, sizeof header);
         switch (header.command) {
            // all command cases
            case cix_command::LS: 
               lsout (client_sock, header);
               break;
            case cix_command::GET: 
               send_file (client_sock, header);
               break;
            case cix_command::PUT: 
               put_file (client_sock, header);
               break;
            case cix_command::RM: 
               remove_file (client_sock, header);
               break;

            default:
               break;
         }
      }
   }catch (socket_error& error) {
   }catch (cix_exit& error) {
   }
   throw cix_exit();
}

void fork_cixserver (server_socket& server, accepted_socket& accept) { 
   pid_t pid = fork();
   if (pid == 0) {    // now running child
      server.close(); // child only listens to one client 
      run_server (accept);
      throw cix_exit();
   }else {
      accept.close();
      if (pid < 0) {
      }else {
      }
   }
}


void reap_zombies() {
   for (;;) { // want to get all child processes
      int status;
      pid_t child = waitpid (-1, &status, WNOHANG);
      if (child <= 0) break;
      kill(child, SIGKILL);
   }
}

void signal_handler (int signal) {
   reap_zombies();
}

void signal_action (int signal, void (*handler) (int)) {
   struct sigaction action;
   action.sa_handler = handler;
   sigfillset (&action.sa_mask);
   action.sa_flags = 0;
   int rc = sigaction (signal, &action, nullptr);
}


// complete
int main (int argc, char** argv) {
   log.execname (basename (argv[0]));
   vector<string> args (&argv[1], &argv[argc]);
   signal_action (SIGCHLD, signal_handler);
   in_port_t port = get_cix_server_port (args, 0); // listener port
   try {
      server_socket listener (port);
      for (;;) {
         accepted_socket client_sock; // client socket
         for (;;) {
            try {
               listener.accept (client_sock);
               break;
            }catch (socket_sys_error& error) {
               switch (error.sys_errno) {
                  case EINTR: 
                     break;
                  default:
                     throw;
               }
            }
         }
         // socket was accepted, fork sub process
         try {
            fork_cixserver (listener, client_sock);
            reap_zombies(); // clean sub processes
         }catch (socket_error& error) {
            log << error.what() << endl;
         }
      }
   }catch (socket_error& error) {
   }catch (cix_exit& error) {
      system("pkill cix");
   }
   return 0;
}





