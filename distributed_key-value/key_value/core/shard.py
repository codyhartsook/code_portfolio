# partitioning algorithm
# implements consistent hashing with virtual nodes

# procedure
# 1. hash nodes by IP address
# 2. hash "data" by key

# each data packet corresponds to a node on a unit circle of integers
# ownership of data is defined as:
#	the predecessor on the circle
#	the data between two nodes on the circle

import xxhash as hasher
import random, string
from bisect import bisect_left
from database import Database # want to be able to use Database methods

# create a shard given database class
class Partition(Database):
	"""docstring for consistent_hash class"""
	def __init__(self, IP, view):
		Database.__init__(self)
		self.virtual_range = 10
		self.IP = IP
		self.Physical_Nodes = view
		self.VIEW = []
		self.LABELS = {}
		self.initial_view(view)

	# construct initial view given ip/port pairs
	# use concept of virtual nodes
	def initial_view(self, view):

		unsorted_list = []

		# insert ip addresses into dict
		for ip_port in view:
			for v_num in range(self.virtual_range):

				virtural_node = ip_port + str(v_num)
				ring_num = hasher.xxh32(virtural_node).digest() # unique value on "ring"

				unsorted_list.append(ring_num)
				self.LABELS[ring_num] = ip_port

		# we want to store ring values in sorted list
		self.VIEW = unsorted_list.sort()

	# perform a key operation, ie find the correct node given key
	def key_op(self, key):
		
		ring_val = hasher.xxh32(key).digest()

		node_ring_val = self.find_node(ring_val) 
		ip_port = self.LABELS[node_ring_val]

		return ip_port

	# return list of nodes to query which can be done in app
	def key_count(self):
		return self.Physical_Nodes

	# respond to view change request, perform a reshard
	# this can only be done if all nodes have been given new view
	def view_change(self, new_view):

		new_physical_view = self.update_view(new_view) # add or remove nodes

		self.reshard(new_physical_view) # reshard 

	# perform a reshard, re-distribute minimun number of keys
	def reshard(self, new_physical_view):
		pass
		
	def update_view(self, new_view):
		# are we adding a new node to the current view
		if len(new_view) > len(self.Physical_Nodes):
			new_nodes = []

			for ip_port in new_view:
				if ip_port not in self.Physical_Nodes:
					new_nodes.append(ip_port)

			# do something with new_nodes

		# if we are removing node from the current view
		elif len(new_view) < len(self.Physical_Nodes):
			pass

		# must be replacing a node 
		else:
			pass

	# perform binary search on VIEW given ring value
	# we need to be careful about wrap around case. If ring_val is max_int, wrap to 0
	def find_node(self, ring_val):

		if abs(ring_val) == (2 ** 31 - 1):
			print("must wrap around") 
			node_num = sel.VIEW[0]
			return node_num

		node_num = self.VIEW[bisect_right(self.VIEW, ring_val)] 
		return node_num




		