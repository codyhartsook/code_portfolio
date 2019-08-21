# network management

import socket
import os
import pickle
import random
import protocol 
import KD_Tree as kdtree

# -----------------------------------------------------------------------------
# compute servers will connect to the network server and their ip and location
# will be stored here

# clients will connect to the network and be paired with an active compute server
# -----------------------------------------------------------------------------
class Network_Server():
	def __init__(self):
		self.num_servers = 0
		self.MAX = 12500
		self.client_buffer = []
		self.port = 7876
		self.host = ""
		self.Network = kdtree.create(dimensions=3) # create empty tree
		self.set_ip()

	def set_ip(self):
		#hostname = socket.gethostname()
		# get the according IP address
		#ip_address = socket.gethostbyname(hostname)
		ip_address = "10.0.0.114"
		self.host = ip_address

	def add_server(self, server):
		print("adding compute engine to network")

		#safe = authenticate(server)
		safe = True
		if safe:
			server.State = 0 # idle
			self.Network.add(server)

	def remove_server(self, server):
		safe = self.in_use(server)
		if safe:
			point = (server.Long, server.Lat, server.Z)
			self.Network.remove(point)
		else:
			print("must finish task or force leave")

	# update the network every x minutes
	# recompute min spanning tree as electricity prices fluctuate
	def update_network(self):
		pass

	# determine if the server is currently working
	def in_use(self, server):
		return server.State

	# we have found a server match for the client, now we need to connect them
	def connect_peers(self, client, server):
		pass

	def find_compute_engine(self, client):

		if len(self.client_buffer) > 0:
			self.client_buffer.append(client)
			client = self.client_buffer.pop(0)

		X = client.Long
		Y = client.Lat
		Z = self.MAX # set to max operating distance

		server = self.find_weighted_closest(X, Y, Z, 4) #  find 4 closest servers

		# connect client to compute engine
		self.connect_peers(client, server)

	# find weighted closest server
	def find_weighted_closest(self, X, Y, Z, k):
		print("find_weighted_closest compute engine")
		point = (X, Y, Z)

		servers = self.Network.search_knn(point, k) # find 4 nearest
		print(servers)
		for engine in servers:
			ref = engine.ID
			print("comp Longitude:", engine.Long)
			print("comp Latitude:", engine.Lat)

			if ref.state == 0:
				ref.State = 1  # does this update in tree 
				return ref

	# store compute servers in network
	# connect clients to compute servers
	def handle_clients(self, S, addr):
		
		try:

			data = S.recv(4096) # recieve entire object
			object_var = pickle.loads(data)
			msg = object_var.Title

			if msg == "client":
				self.find_compute_engine(object_var)
			elif msg == "engine":
				self.add_server(object_var)
			else:
				print("false msg")

		except:
			print("error occured recieving client data")

	# entry point: run the server and fork a process when a client connects
	def run_server(self):
		S = socket.socket()
		S.bind((self.host, self.port)) # listen to requests on given port
		S.listen(10)

		print("network server is up and listening")

		while True:

			try:

				# accept the client a fork a process to handle it
				conn, addr = S.accept()
				child_pid = os.fork()

				if child_pid == 0: # succesfully connnected
					self.handle_clients(conn, addr)
					conn.close()
					break

			except Exception as e:
				print("\nshutting down network server")
				print(e)
				break

if __name__ == "__main__":

	master_server = Network_Server()
	master_server.run_server()














