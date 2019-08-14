# Decentralized Cloud Computing Network Project
# Status: in progress
__author__ Cody Hartsook

import random
import socket
import protocol

# -----------------------------------------------------------------------------
# network's compute engine ID
# this allows the network to keep track of it's availiable servers/engines
# -----------------------------------------------------------------------------
class Compute_Engine_Ref():
	def __init__(self, ip, longitude, latitude, Pr_Power):
		self.Long = longitude
		self.Lat = latitude
		self.Pr_Power = Pr_Power
		self.State = None

		self.my_ip = ip
		self.peer_ip = ""
		self.peer_port = None

	def __str__(self):
		string = "long: "+str(self.Long)+", lat: "+str(self.Lat)+", Power: "+\
			str(self.Pr_Power)+", key:"+str(self.Long+self.Lat)
		return string

	def update(self, grid):
		pass

# -----------------------------------------------------------------------------
# network's client ID class
# this is a server side class
# -----------------------------------------------------------------------------
class Client_Ref():
	def __init__(self, ip, Long, Lat, ic, cpi, Priority):
		self.Long = Long
		self.Lat = Lat
		self.I_C = ic
		self.CPI = cpi
		self.Priority = Priority
		self.Done = False
		self.Elapsed = None

		self.my_ip = ""
		self.peer_ip = ""
		self.peer_port = None

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
		self.random_init()

	def set_ip(self):
		#local_hostname = socket.gethostname()
		#local_fqdn = socket.getfqdn()
		# get the according IP address
		#ip_address = socket.gethostbyname(local_fqdn)
		ip_address = "10.0.0.114"

		self.my_ip = ip_address

	def random_init(self):
		self.Long = random.randint(0, 360)
		self.Lat = random.randint(0, 180)

		self.I_C = random.randint(1000, 50000)
		self.CPI = random.randint(2, 6)
		self.Priority = random.randint(0, 3)

	def manual_init(self):
		pass

	def read(self, S):
		pass

	def write(self, message, S):
		pass

	def network_server_connection(self):
		print("connecting to network")

		while True:

			S = socket.socket()
			S.connect((self.network_ip, self.network_port))

			msg = "client_connect,"
			msg += str(self.my_ip) + ","
			msg += str(self.Long) + ","
			msg += str(self.Lat) + ","
			msg += str(self.I_C) + ","
			msg += str(self.CPI) + ","
			msg += str(self.Priority)
			encoded_msg=bytes(msg, "utf-8")
			S.send(encoded_msg)
			break

	def peer_connection(self):
		if self.peer_port == None:
			print("connot connect to peer before network server")
		else:
			pass

# -----------------------------------------------------------------------------
# Define an end-user compute_engine / local computer
# This is is local class with a UI
# -----------------------------------------------------------------------------
class Compute_Engine():
	def __init__(self):
		self.Long = None
		self.Lat = None
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

	def random_init(self):
		self.Long = random.randint(0, 360)
		self.Lat = random.randint(0, 180)

		self.Pr_Power = random.randint(1, 10)

	def manual_init(self):
		pass

	def read(self, S):
		pass

	def write(self, message, S):
		pass

	def network_server_connection(self):

		while True:

			S = socket.socket()
			S.connect((self.network_ip, self.network_port))

			msg="register_comp,"
			msg += self.my_ip + ","
			msg += str(self.Long) + ","
			msg += str(self.Lat) + ","
			msg += str(self.Pr_Power)
			encoded_msg=bytes(msg, "utf-8")
			S.send(encoded_msg)
			break

	def peer_connection(self):
		if self.peer_port == None:
			print("connot connect to peer before network server")
		else:
			pass

	def compute(task):
		pass























