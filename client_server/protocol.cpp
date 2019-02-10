// $Id: protocol.cpp,v 1.7 2018-07-12 17:39:08-07 - - $

#include <cassert>
#include <string>
#include <unordered_map>
using namespace std;

#include "protocol.h"

struct cix_hasher { // takes key and converts to int
   size_t operator() (cix_command cmd) const {
      return static_cast<uint8_t> (cmd); // cast uint8
   }
};

const unordered_map<cix_command,string,cix_hasher> cix_command_map {
   {cix_command::ERROR, "ERROR"},
   {cix_command::EXIT , "EXIT" },
   {cix_command::GET  , "GET"  },
   {cix_command::HELP , "HELP" },
   {cix_command::LS   , "LS"   },
   {cix_command::PUT  , "PUT"  },
   {cix_command::RM   , "RM"   },
   {cix_command::FILE , "FILE" },
   {cix_command::LSOUT, "LSOUT"},
   {cix_command::ACK  , "ACK"  },
   {cix_command::NAK  , "NAK"  },
};


void send_packet (base_socket& socket,
                  const void* buffer, size_t bufsize) {
   assert (sizeof (cix_header) == HEADER_SIZE);
   const char* bufptr = static_cast<const char*> (buffer);
   ssize_t ntosend = bufsize;
   do {
      ssize_t nbytes = socket.send (bufptr, ntosend);
      if (nbytes < 0) throw socket_sys_error (to_string (socket));
      bufptr += nbytes;
      ntosend -= nbytes;
   }while (ntosend > 0);
}

void recv_packet (base_socket& socket, void* buffer, size_t bufsize) {
   assert (sizeof (cix_header) == HEADER_SIZE);
   char* bufptr = static_cast<char*> (buffer);
   ssize_t ntorecv = bufsize;
   do {
      ssize_t nbytes = socket.recv (bufptr, ntorecv);
      if (nbytes < 0) throw socket_sys_error (to_string (socket));
      if (nbytes == 0) throw socket_error (to_string (socket)
                                           + " is closed");
      bufptr += nbytes;
      ntorecv -= nbytes;
   }while (ntorecv > 0);
}


ostream& operator<< (ostream& out, const cix_header& header) {
   const auto& itor = cix_command_map.find (header.command);
   string code = itor == cix_command_map.end() ? "?" : itor->second;
   cout << "{" << header.nbytes << "," << unsigned (header.command)
        << "(" << code << "),\"" << header.filename << "\"}";
   return out;
}    

string get_cix_server_host (const vector<string>& args, size_t index) {
   if (index < args.size()) return args[index];
   char* host = getenv ("CIX_SERVER_HOST");
   if (host != nullptr) return host;
   return "localhost";
}

in_port_t get_cix_server_port (const vector<string>& args,
                               size_t index) {
   string port = "-1";
   if (index < args.size()) port = args[index];
   else {
      char* envport = getenv ("CIX_SERVER_PORT");
      if (envport != nullptr) port = envport;
   }
   return stoi (port);
}


