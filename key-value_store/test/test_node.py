import unittest
import collections
from node import Node
from Message import Router
import random
import string

# example node addresses
addr1="10.10.0.2:13800"
addr2="10.10.0.3:13800"
addr3="10.10.0.4:13800"
addr4="10.10.0.5:13800"
addr5="10.10.0.6:13800"
addr6="10.10.0.7:13800"

# instanciate node class
router = Router()
repl_factor = 2

class Test_Shard_Methods(unittest.TestCase):

	def randomString(self, stringLength=10):
	    """Generate a random string of fixed length """
	    letters = string.ascii_lowercase
	    return ''.join(random.choice(letters) for i in range(stringLength))

	def test_insert_key(self):
		print('\ntest0 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4]
		shard = Node(router, addr1, view, repl_factor)

		shard1_count = 0
		shard2_count = 0

		for key in range(100):
			keyName = 'key' + str(key)
			#print(keyName)
			val = 'value' + str(key)
			match = shard.find_match(keyName)
			
			if match == 0:
				shard1_count += 1
			else:
				shard2_count += 1

		print('shard0 was sent', shard1_count, 'keys')
		print('shard1 was sent', shard2_count, 'keys')
		#print('response:', res)

	'''def test_initial_state(self):
		print('\ntest1 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4]
		shard = Node(router, addr1, view, repl_factor)
		#print(shard)
		self.assertTrue(shard != None)

	def test_view_change_add_node(self):
		print('\ntest2 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4]
		shard = Node(router, addr1, view, repl_factor)
		#print(shard)
		old_card = len(shard.nodes)
		new_view = view.copy()
		new_view.append(addr5)

		shard.view_change(new_view, repl_factor)
		new_card = len(shard.nodes)

		#print(shard)
		self.assertTrue(new_card>old_card)

	def test_view_change_remove_node(self):
		print('\ntest3 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4, addr5]
		shard = Node(router, addr1, view, repl_factor)
		#print(shard)
		old_card = len(shard.nodes)
	
		new_view = [addr1, addr2, addr3, addr4]

		shard.view_change(new_view, repl_factor)
		new_card = len(shard.nodes)
		#print(shard)
		self.assertTrue(new_card<old_card)

	def test_view_change_add_shard(self):
		print('\ntest4 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4]
		shard = Node(router, addr1, view, repl_factor)
		#print(shard)
		old_card = len(shard.P_SHARDS)
		new_view = view.copy()
		new_view.append(addr5)
		new_view.append(addr6)

		shard.view_change(new_view, repl_factor)

		new_card = len(shard.P_SHARDS)
		#print(shard)
		self.assertTrue(new_card>old_card)

	def test_view_change_remove_shard(self):
		print('\ntest5 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4, addr5, addr6]
		shard = Node(router, addr1, view, repl_factor)
		#print(shard)

		old_card = len(shard.P_SHARDS)
		new_view = [addr1, addr2, addr3, addr4]

		shard.view_change(new_view, repl_factor)

		new_card = len(shard.P_SHARDS)
		#print(shard)
		self.assertTrue(old_card>new_card)

	def test_view_change_transfer_keys(self):
		print('\ntest5 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4]
		shard = Node(router, addr1, view, repl_factor)
		
		for key in range(20):
			keyName = 'key' + str(key)
			val = 'value' + str(key)
			shard.insertKey(keyName, val, {})


		new_view = [addr1, addr2, addr3, addr4, addr5, addr6]

		shard.view_change(new_view, repl_factor)

		print(shard)'''


	def test_view_change_remove_self(self):
		print('\ntest5 ----------------------------------------------------------')
		view = [addr1, addr2, addr3, addr4, addr5, addr6]
		shard = Node(router, addr1, view, repl_factor)

		new_view = [addr2, addr3, addr4, addr5]

		shard.view_change(new_view, repl_factor)



if __name__ == '__main__':
	unittest.main()








