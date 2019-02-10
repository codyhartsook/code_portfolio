// $Id: cix.cpp,v 1.6 2018-07-26 14:18:32-07 - - $
// client module - communicates with server daemon

#include <iostream>
#include <fstream> 
#include <string>
#include <vector>
#include <unordered_map>
using namespace std;

#include <libgen.h>
#include <sys/types.h>
#include <unistd.h>

#include "protocol.h"
#include "logstream.h"
#include "sockets.h"

vector<string> split (const string& line, const string& delimiters) {
   vector<string> words;
   size_t end = 0;

   // Loop over the string, splitting out words, and for each word
   // thus found, append it to the output wordvec.
   for (;;) {
      size_t start = line.find_first_not_of (delimiters, end);
      if (start == string::npos) break;
      end = line.find_first_of (delimiters, start);
      words.push_back (line.substr (start, end - start));
   }
   return words;
}


logstream log (cout);
struct cix_exit: public exception {};

unordered_map<string,cix_command> command_map { 
   {"exit", cix_command::EXIT},
   {"help", cix_command::HELP},
   {"ls"  , cix_command::LS  },
   {"get" , cix_command::GET },
   {"put" , cix_command::PUT },
   {"rm"  , cix_command::RM  },
};

// raw help string
static const string help = R"||(
exit         - Exit the program.  Equivalent to EOF.
get filename - Copy remote file to local host.
help         - Print help summary.
ls           - List names of files on remote server.
put filename - Copy local file to remote host.
rm filename  - Remove file from remote server.
)||";

void cix_help() { 
   cout << help;
}

// get specified file from remote server
void cix_get(string filename, client_socket& server) {
   cix_header header;
   header.command = cix_command::GET;

   // send request for file
   strncpy(header.filename, filename.c_str(), sizeof(header.filename));
   send_packet(server, &header, sizeof header);

   // get the server command status and the header.nbytes
   recv_packet(server, &header, sizeof header);
   if (header.command == cix_command::NAK){
      log << "server could not find file" << endl;
      throw cix_exit();
   }

   // get the file contents now that we have size of file
   char buffer[header.nbytes];
   recv_packet (server, buffer, header.nbytes);

   if (header.command != cix_command::ACK){
      log << "sent get, server did not return ack" << endl;
      throw cix_exit();
   }

   // convert buffer to string   
   string str_file;
   for (unsigned int i=0; i<header.nbytes; ++i){
      str_file += buffer[i];
   }

   // write to new file
   ofstream new_file;
   new_file.open (filename.c_str());
   new_file << str_file;

}

void cix_put(string filename, client_socket& server) {
   // put specified file in remote server
   cix_header header;
   header.command = cix_command::PUT;

   ifstream is (filename, ifstream::binary);
   if (is) {
      
      is.seekg (0, is.end);
      int length = is.tellg();
      is.seekg (0, is.beg);
      
      char * buffer = new char [length];
      is.read (buffer,length);

      if (not is) {
         log << "error occured in reading file" << endl;
         throw cix_exit();
      }
      is.close();

      // send header with just filename
      header.nbytes = strlen(buffer);
      strncpy(header.filename,filename.c_str(),sizeof(header.filename));
      // send payload
      send_packet(server, &header, sizeof header);
      send_packet(server, buffer, header.nbytes);
      recv_packet(server, &header, sizeof header);

      if (header.command != cix_command::ACK){
         log << "sent put, server did not return ack" << endl;
         throw cix_exit();
      }

      delete[] buffer;
   }
}

void cix_rm(string filename, client_socket& server) {
   // remove specified file from remote server
   cix_header header;
   header.command = cix_command::RM;

   strncpy(header.filename, filename.c_str(), sizeof(header.filename));
   send_packet(server, &header, sizeof header);
   recv_packet(server, &header, sizeof header);

   if (header.command != cix_command::ACK){
      //log << "server could not remove file" << endl;
      //throw cix_exit();
   }
}

// sends header to cixd, server responds
void cix_ls (client_socket& server) {
   cix_header header;
   header.command = cix_command::LS;
   send_packet (server, &header, sizeof header);
   recv_packet (server, &header, sizeof header);
   if (header.command != cix_command::LSOUT) {
      log << "error in retrivieving contents of server" << endl;
      throw cix_exit();
   }else {
      char buffer[header.nbytes + 1]; // add one for null plug
      recv_packet (server, buffer, header.nbytes);
      buffer[header.nbytes] = '\0';
      cout << buffer;
   }
}


void usage() {
   cerr << "Usage: " << log.execname() << " [host] [port]" << endl;
   throw cix_exit();
}

int main (int argc, char** argv) {
   log.execname (basename (argv[0]));
   vector<string> args (&argv[1], &argv[argc]);
   if (args.size() > 2) usage();
   string host = get_cix_server_host (args, 0);
   in_port_t port = get_cix_server_port (args, 1);
   log << to_string (hostinfo()) << endl;
   try {
      log << "connecting to " << host << " port " << port << endl;
      client_socket server (host, port);
      log << "connected to " << to_string (server) << endl;
      for (;;) {
         string line;
         getline (cin, line);
         // if line contains more than one argument, split it
         vector<string> line_cmd = split (line, " \t");

         if (cin.eof()) throw cix_exit();

         const auto& itor = command_map.find (line_cmd.at(0));
         cix_command cmd = itor == command_map.end()
                         ? cix_command::ERROR : itor->second;
         // execute one of the commands
         switch (cmd) { 
            case cix_command::EXIT:
               throw cix_exit();
               break;
            case cix_command::HELP:
               cix_help();
               break;
            case cix_command::LS:
               cix_ls (server);
               break;
            case cix_command::PUT:
               cix_put(line_cmd.at(1), server);
               break;
            case cix_command::GET:
               cix_get(line_cmd.at(1), server);
               break;
            case cix_command::RM:
               cix_rm(line_cmd.at(1), server);
               break;
            default:
               log << line << ": invalid command" << endl;
               break;
         }
      }
   }catch (socket_error& error) {
      log << error.what() << endl;
   }catch (cix_exit& error) {
   }
   return 0;
}
