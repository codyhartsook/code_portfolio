# network management

import socket
import os
import random
import protocol 
import my_kd_tree as kdtree
from system_core import Compute_Engine_Ref, Client_Ref, Grid

# -----------------------------------------------------------------------------
# compute servers will connect to the network server and their ip and location
# will be stored here

# clients will connect to the network and be paired with an active compute server
# -----------------------------------------------------------------------------
class Network_Server():
	def __init__(self):
		self.num_servers = 0
		self.network = []
		self.client_buffer = []
		self.port = 7876
		self.host = ""
		self.KD_Tree = kdtree.create(dimensions=3) # create empty tree
		self.set_ip()

	def set_ip(self):

		#hostname = socket.gethostname()
		# get the according IP address
		#ip_address = socket.gethostbyname(hostname)
		ip_address = "10.0.0.114"
		self.host = ip_address

	# define a function which maps electricity cost to a discrete value
	# this is used to define the third dimension of a point x, y, z
	def energy_bias(server):
		return 1

	def add_server(self, str_obj):
		print("adding compute engine to network")
		print(str_obj)

		server = Compute_Engine_Ref(str_obj[1], str_obj[2], str_obj[3], str_obj[4])

		#safe = authenticate(server)
		safe = True
		if safe:
			server.State = 0 # idle
			x = server.Long
			y = server.Lat
			z = self.energy_bias(x, y)
			server.Z = z

			point = (x, y, z)
			ID = server   # store a reference to the compute engine

			self.KD_Tree.add(point, ID)

	def remove_server(self, server):
		safe = self.in_use(server)
		if safe:
			point = (server.Z, server.Y, server.Z)
			self.KD_Tree.remove(point)
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
		port = random.randint(3000, 8000)
		server_ip = server.my_ip
		client_ip = server

		return server_ip, port

	def find_compute_engine(self, str_obj):
		print("connecting a client to a compute engine")
		print(str_obj)

		client = Client_Ref(str_obj[1], str_obj[2], str_obj[3], str_obj[4], str_obj[5], str_obj[6])

		if len(self.client_buffer) > 0:
			self.client_buffer.append(client)
			client = self.client_buffer.pop(0)

		X = client.Long
		Y = client.Lat
		Z = 12000 # set to max operating distance

		server = self.find_weighted_closest(X, Y, Z, 4) #  find 4 closest servers

		# connect client to compute engine
		# send ip and port to both server and client
		self.connect_peers(ip, port, client, server)

	# find weighted closest server
	def find_weighted_closest(self, X, Y, Z, k):
		print("find_weighted_closest compute engine")
		point = (X, Y, Z)

		servers = self.KD_Tree.search_knn(point, k) # find 4 nearest
		for engine in servers:
			ref = engine.ID
			if ref.state == 0:
				ref.State = 1  # does this update in tree 
				return ref

		# all compute engines are busy, do a broader search
		self.find_weighted_closest(X, Y, Z, k*2)

	# store compute servers in network
	# connect clients to compute servers
	def handle_clients(self, S, addr):
		
		while True:

			data = S.recv(64)
			decoded = data.decode("utf-8")
			if not decoded:
				break
			else:
				msg = decoded.split(",")
				role = protocol.handle_message(msg)
				if role == False:
					break
				elif role == "engine":
					self.add_server(msg)
				else:
					self.find_compute_engine(msg)

					# send client ip and port to communicate with compute engine

			break

	# entry point: run the server and fork a process when a client connects
	def run_server(self):
		S = socket.socket()
		S.bind((self.host, self.port)) # listen to requests on given port
		S.listen(10)

		print("network server is up and listening")

		while True:

			try:

				client, addr = S.accept()
				child_pid = os.fork()

				if child_pid == 0: # succesfully connnected
					self.handle_clients(client, addr)
					break

			except Exception as e:
				print("\nshutting down network server")
				print(e)
				break

if __name__ == "__main__":

	master_server = Network_Server()
	#master_server.run_server()

	point = (1, 2, 12)
	ID = 'obj1'

	point2 = (4, 5, 6)
	ID2 = 'obj2'

	master_server.KD_Tree.add(point, ID)
	master_server.KD_Tree.add(point2, ID2)
	kdtree.visualize(master_server.KD_Tree)

	local = (4, 5, 12)
	node = master_server.KD_Tree.search_knn(local, 1)
	print(node)













