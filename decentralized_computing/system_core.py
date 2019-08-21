# Decentralized Cloud Computing Network Project
# Status: in progress

import random
import socket
import protocol
import pickle

# -----------------------------------------------------------------------------
# this class will utilize third party APIs in order to get local electricity
# pricing as well as supply and demand.
# -----------------------------------------------------------------------------
class Grid():
	def __init__(self):
		self.micro_grids = []

		self.Demand = None
		self.Supply = None
		self.E_price = None
		self.Long = None
		self.Lat = None

class micro_grid(Grid):
	def __init__(self):
		pass

# -----------------------------------------------------------------------------
# Define an end-user client
# This is is local class with a UI
# -----------------------------------------------------------------------------
class Client():
	def __init__(self):
		self.Title = "client"
		self.ID = None
		self.Long = None
		self.Lat = None
		self.I_C = None
		self.CPI = None
		self.Priority = None
		self.Done = False
		self.Elapsed = None

		self.my_ip = ""
		self.network_ip = "10.0.0.114"
		self.peer_ip = ""
		self.network_port = 7876
		self.peer_port = None
		self.set_ip()
		self.test()

	def set_ip(self):
		#local_hostname = socket.gethostname()
		#local_fqdn = socket.getfqdn()
		# get the according IP address
		#ip_address = socket.gethostbyname(local_fqdn)
		ip_address = "10.0.0.114"
		self.my_ip = ip_address

	def test(self):
		self.Long = random.randint(0, 360)
		self.Lat = random.randint(0, 180)

		self.I_C = random.randint(1000, 50000)
		self.CPI = random.randint(2, 6)
		self.Priority = random.randint(0, 3)

	# remotely run an application or program
	def run(self, Application):
		pass

	# get an estimate of how intensive the given application is to run
	def computational_intensity(self, Application):
		pass

# -----------------------------------------------------------------------------
# Define an end-user compute_engine / local computer
# This is is local class with a UI
# -----------------------------------------------------------------------------
class Compute_Engine():
	def __init__(self):
		self.Title = "engine"
		self.Long = None
		self.Lat = None
		self.Z = None
		self.coords = None
		self.Pr_Power = None
		self.State = None
		self.ID = None
		self.Virtual_Machine = None

		self.my_ip = ""
		self.network_ip = "10.0.0.114"
		self.peer_ip = ""
		self.network_port = 7876
		self.peer_port = None
		self.set_ip()
		self.random_init()

	def set_ip(self):
		#local_hostname = socket.gethostname()
		#local_fqdn = socket.getfqdn()
		# get the according IP address
		#ip_address = socket.gethostbyname(local_fqdn)
		ip_address = "10.0.0.114"
		self.my_ip = ip_address

	def __len__(self):
		return len(self.coords)

	def __getitem__(self, i):
		return self.coords[i]

	def __repr__(self):
		return 'Compute_Engine({}, {}, {})'.format(self.coords[0], self.coords[1], self.coords[2])

	# define a function which maps electricity cost to a discrete value
	# this is used to define the third dimension of a point x, y, z
	def energy_bias(self, server):
		self.Z = random.randint(0, 360)

	def random_init(self):
		self.Long = random.randint(0, 360)
		self.Lat = random.randint(0, 180)
		self.coords = (self.Long, self.Lat, self.Z)
		self.Pr_Power = random.randint(1, 10)

	# sign up local machine as a compute server
	def register_machine(self):
		pass

	# run the application or program 
	def run(self, application):
		pass

# -----------------------------------------------------------------------------
# Define an end-user compute_engine / local computer
# This is is local class with a UI
# -----------------------------------------------------------------------------
class Engine_UI():
	def __init__(self):
		self.Virtual_Machine = None
		self.Agent = Compute_Engine()

	def connect_to_network(self):
			
		self.Agent.energy_bias() # sets agents z coor

		try:
			
			S = socket.socket()
			S.connect((self.Agent.network_ip, self.Agent.network_port))

			Agent_Pickle = pickle.dumps(self.Agent)
			S.send(Agent_Pickle)

		except:
			print("error occured when connecting engine to network")

	def peer_connection(self):
		if Agent.peer_port == None:
			print("connot connect to peer before network server")
		else:
			pass

# -----------------------------------------------------------------------------
# Define an end-user client
# This is is local class with a UI
# -----------------------------------------------------------------------------
class Client_UI():
	def __init__(self):
		self.Agent = Client()

	def connect_to_network(self):

		try:

			S = socket.socket()
			S.connect((self.Agent.network_ip, self.Agent.network_port))

			Agent_Pickle = pickle.dumps(self.Agent)
			S.send(Agent_Pickle)

		except:
			print("error occured when connecting client to network")

	def peer_connection(self):
		if Agent.peer_port == None:
			print("connot connect to peer before network server")
		else:
			pass





























