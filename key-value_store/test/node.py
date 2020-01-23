'''
Partitioning algorithm implementing consistent hashing, virtual nodes
and shard membership.
'''

import xxhash as hasher
from bisect import bisect_right, bisect_left
from datetime import datetime
import json
import time
from collections import OrderedDict
from storage_host import KV_store
from vectorclock import VectorClock
#from apscheduler.scheduler import Scheduler
import random
import sys

class Node(KV_store):
	'''docstring for node class'''
	def __init__(self, router, address, view, replication_factor):
		KV_store.__init__(self, address)
		self.gossipScheduled = False
		self.lastToGossip = False
		self.gossiping = False
		#self.sched = Scheduler()
		#self.sched.start()
		self.history = [('Initialized', datetime.now())]
		self.ADDRESS = address
		self.VC = VectorClock(view=view, clock=None)
		self.ring_edge = 691 if len(view) < 100 else 4127    # parameter for hash mod value
		self.repl_factor = replication_factor
		self.num_shards = 0
		self.virtual_range = 16       
		self.shard_interval = self.ring_edge // self.virtual_range
		self.nodes = []
		self.shard_ID = -1
		self.V_SHARDS = [] # store all virtual shards
		self.P_SHARDS = [[] for i in range(0, self.num_shards)] # map physical shards to nodes
		self.virtual_translation = {} # map virtual shards to physical shards
		self.backoff_mod = 59
   
		self.router = router
		self.view_change(view, replication_factor)

	def __repr__(self):
		return {'ADDRESS':self.ADDRESS, 'shard_ID':self.shard_ID, 'P_SHARDS':self.P_SHARDS, 'KEYS':self.keystore}

	def __str__(self):
		return 'ADDRESS: '+self.ADDRESS+'\nshard_ID: '+str(self.shard_ID)+'\n: '+(', '.join(map(str, self.keystore))) + '\nP_SHARDS: ' + (', '.join(map(str, self.P_SHARDS)))

	'''
	give a state report 
	this includes node data and distribution of keys to nodes
	'''
	def state_report(self):
		state = self.__repr__()

		state['HISTORY'] = {}
		string = 'node'
		itr = 1
		for event in self.history:
			key = string + str(itr)
			itr += 1
			state['HISTORY'][key] = event

		return state

	'''
	return all physical shards
	'''
	def all_shards(self):
		return self.P_SHARDS

	def all_nodes(self):
		return self.nodes

	'''
	get all nodes in this shard
	'''
	def shard_replicas(self, shard_ID):
		return self.P_SHARDS[shard_ID]

	'''
	hash frunction is a composit of xxhash modded by prime
	'''
	def hash(self, key):
		hash_val = hasher.xxh32(key).intdigest()

		# may be expensive but will produce better distribution
		return (hash_val % self.ring_edge)


	'''
	evenly distribute nodes into num_shard buckets
	'''
	def even_distribution(self, repl_factor, nodes):

		nodes.sort()
		num_shards = (len(nodes) // repl_factor)
		replicas = (len(nodes) // num_shards)
		overflow = (len(nodes) % num_shards)

		shards = [[] for i in range(0, num_shards)]

		node_iter = 0
		for shard in range(num_shards):
			extra = (1 if shard < overflow else 0)
			interval = replicas + extra

			shards[shard] = nodes[node_iter:(node_iter+interval)]
			node_iter += interval

		return shards

	'''
	Perform a key operation, ie. find the correct shard given key.
	First hash the key then perform binary search to find the correct shard
	to store the key. 
	'''
	def find_match(self, key):
		
		ring_val = self.hash(key)
		# get the virtual shard number
		v_shard = self.find_shard('predecessor', ring_val)
		# convert to physical shard
		shard_ID = self.virtual_translation[v_shard]

		return shard_ID

	'''
	perform binary search on list of virtual shards given ring value
	we need to be careful about wrap around case. If ring_val >= max_ring_val, return 0
	'''
	def find_shard(self, direction, ring_val):
		if direction == 'predecessor':
			v_shard = bisect_left(self.V_SHARDS, ring_val)
			if v_shard:
				return self.V_SHARDS[v_shard-1]
			return self.V_SHARDS[-1]

		elif direction == 'successor':
			v_shard = bisect_right(self.V_SHARDS, ring_val)
			if v_shard != len(self.V_SHARDS):
				return self.V_SHARDS[v_shard]
			return self.V_SHARDS[0]

	'''
	respond to view change request, perform a reshard
	this can only be done if all nodes have been given new view
	2 cases:
		1. len(nodes) + 1 // r > or < shard_num: we need to add or 
			remove a shard to maintain repl_factor
		2. add and/or remove nodes
	'''
	def view_change(self, view, repl_factor):
		new_num_shards = len(view) // repl_factor
		
		# we should always have more than one shard
		if new_num_shards == 1:
			new_num_shards = 2

		buckets = self.even_distribution(repl_factor, view)

		# add nodes and shards
		for shard in range(len(buckets)):

			if self.ADDRESS in buckets[shard]:
				self.shard_ID = shard
				
				#if not self.gossipScheduled:
				#	self.sched.add_interval_job(self.gossip, seconds=self.gossip_backoff())
				#	self.gossipScheduled = True

			if shard >= len(self.P_SHARDS):
				self.add_shard(buckets[shard])

			else:
				self.update_shard(buckets[shard], shard)

		# remove empty shards
		for shard_ID in range(len(buckets), len(self.P_SHARDS)):
			self.remove_shard(shard_ID)

		for old_node in list(set(self.nodes) - set(view)):
			self.nodes.pop(self.nodes.index(old_node))

	'''
	add shard to view
	'''
	def add_shard(self, nodes):

		#print('adding new shard', file=sys.stderr)

		new_shards = []
		p_shard = self.num_shards

		if p_shard >= len(self.P_SHARDS):
			self.P_SHARDS.append([])

		# if nodes are new, add them to self.nodes and self.P_SHARDS
		for node in nodes:
			if node not in self.nodes:
				self.nodes.append(node)
			if node not in self.P_SHARDS[p_shard]:
				self.P_SHARDS[p_shard].append(node)

		# create virtual shards
		for v_shard in range(self.virtual_range):

			virtural_shard = str(p_shard) + str(v_shard)
			ring_num = self.hash(virtural_shard) # unique value on 'ring'

			# if ring_num is already in list, skip this iteration
			if ring_num in self.V_SHARDS:
				continue

			self.V_SHARDS.append(ring_num)
			self.virtual_translation[ring_num] = p_shard

			successor = self.find_shard('successor', ring_num)
			predecessor = self.find_shard('predecessor', ring_num)

			# send appropriate keys to v_shard
			if self.virtual_translation[predecessor] == self.shard_ID:
				self.atomic_key_transfer(predecessor, ring_num, successor) 

		self.num_shards += 1
		self.V_SHARDS.sort()

	def update_shard(self, nodes, shard_ID):
		
		for node in self.P_SHARDS[shard_ID]:

			if node not in nodes: # must be getting deleted or moved
				if node == self.ADDRESS: # self is getting deleted
					for new_node in nodes:
						print('moving keys to', new_node, file=sys.stderr)
						success = self.final_state_transfer(new_node)

				self.P_SHARDS[shard_ID].pop(self.P_SHARDS[shard_ID].index(node))			

		for node in nodes:
			if node not in self.nodes:
				self.nodes.append(node)

			if node not in self.P_SHARDS[shard_ID]:
				self.P_SHARDS[shard_ID].append(node)

	'''
	remove from all internal data structures if there are no nodes in shard
	'''
	def remove_shard(self, shard_ID):
		self.P_SHARDS.pop(shard_ID)

	'''
	transfer keys from from self to new shard, according to consistent hashing rules
	'''
	def atomic_key_transfer(self, predecessor, new_shard, successor):
		
		for key in list(self.keystore):
			key_hash = self.hash(key)
			if key_hash < successor and key_hash > predecessor:
				
				shard_destination = self.virtual_translation[new_shard]
				replicas = self.shard_replicas(shard_destination)
				path = '/kv-store/keys/' + str(key) + '/forward'

				data = {'value':self.keystore[key], 'causal-context':{}}
				data = json.loads(json.dumps(data))
				status_code = 400

				print('I should definately send', key, 'to', replicas, file=sys.stderr)
				
				# try to message all replicas, if a replica is unresponsive, ignore it
				for replica in replicas:
					if replica in self.P_SHARDS[self.shard_ID]:
						continue
					print('sending', key, 'to', replica, file=sys.stderr)
					try:
						res = self.router.PUT(replica, path, data)
						status_code = 201
						#except Exception as e:
						#	print('exception caught in atomic_key_transfer:', e, file=sys.stderr)
						#	continue

						# at least one replica responded
						if status_code < 400:
							print('deleting key from my keystore', file=sys.stderr)
							del self.keystore[key]
							if key in self.keystore:
								print('there was a problem deleting the key', file=sys.stderr)
						else:
							print('replicas did not respond when transfering keys', file=sys.stderr)
					except:
						continue

	'''
	send final state of node before removing a node
	'''
	def final_state_transfer(self, node):
		data = {
				"kv-store": self.keystore,
				"causal-context": self.VC.__repr__() 
		}
		replica_ip_addresses = self.shard_replicas(self.shard_ID)
		for replica in replica_ip_addresses:
			if (replica != self.ADDRESS):
				try:
					res = self.router.PUT(replica, '/kv-store/internal/state-transfer', data)
				except:
					continue
				if status_code == 201:
					return True
		return False

	'''
	handle node failures, check if node should be removed or not
	'''
	def handle_unresponsive_node(self, node):
		pass

	def gossip_backoff(self):
		return hash(self.ADDRESS) % random.randint(5,15)

	def gossip(self):

		if (self.gossiping == False) and (not self.lastToGossip) and (self.repl_factor > 1):
			self.lastToGossip = True
			current_key_store = self.keystore
			self.gossiping = True
			replica_ip_addresses = self.shard_replicas(self.shard_ID)
			replica = replica_ip_addresses[(random.randint(0,len(replica_ip_addresses)-1))]
			while (self.ADDRESS == replica):
				replica = replica_ip_addresses[(random.randint(0,len(replica_ip_addresses)-1))]
			myNumber = int((self.ADDRESS.split(".")[3]).split(":")[0])
			otherNumber = int((replica.split(".")[3]).split(":")[0])
			tiebreaker = replica if (otherNumber > myNumber) else self.ADDRESS
			data = {
				"causal-context" : self.VC.__repr__(),
				"kv-store": current_key_store,
				"tiebreaker": tiebreaker
			}
		
			try:
				response = self.router.PUT(replica,'/kv-store/internal/gossip/',json.dumps(data))
				code = response.status_code
			except:
				code = -1

			self.gossiping = False
		








