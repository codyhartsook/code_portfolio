import unittest
import collections
#from Message import Router
import requests
import json

# example node addresses
addr1="10.10.0.2:13800"
addr2="10.10.0.3:13800"
addr3="10.10.0.4:13800"
addr4="10.10.0.5:13800"
addr5="10.10.0.6:13800"
addr6="10.10.0.7:13800"

class Test_API_endpoints(unittest.TestCase):

	# simple system tests
	# -------------------------------------------------------------------------
	
	'''def test_get_key_count(self):
		port = addr1.split(':')[1]
		endpoint = 'http://127.0.0.1:13804/kv-store/key-count'
		headers = {'content-type': 'application/json'}
		payload = '{"causal-context": {}}'

		res = requests.get(endpoint, data=payload, headers=headers)
		if res.ok:
			json_res = res.json()
			print('<key count is', json_res['key_count'], '>')
		else:
			print(res)'''
	
	
	def test_get_ID_and_key_count(self):
		pass

	'''def test_get_shard_info(self):
		shard_ID = 0
		endpoint = 'http://127.0.0.1:13802/kv-store/shards/0'
		headers = {'content-type': 'application/json'}
		payload = json.dumps({"causal-context": {}})

		res = requests.get(endpoint, data=payload, headers=headers)
		print(res)'''

	def test_view_change(self):
		pass

	# key operations
	# -------------------------------------------------------------------------
	def test_insert_new_key(self):
		port = addr1.split(':')[1]
		endpoint = 'http://0.0.0.0:13802//kv-store/keys/sampleKey'
		headers = {'content-type': 'application/json'}
		payload = json.dumps({"value": "sampleValue", "causal-context": {}})

		res = requests.put(endpoint, data=payload, headers=headers)
		if res.ok:
			json_res = res.json()
			print(json_res)
		else:
			print(res)
			return False

	'''def test_update_existing_key(self):
		port = addr1.split(':')[1]
		endpoint = 'http://127.0.0.1:13802/kv-store/keys/sampleKey'
		headers = {'content-type': 'application/json'}
		payload = json.dumps({"value": "sampleValue", "causal-context": {}})

		res = requests.put(endpoint, data=payload, headers=headers)
		if res.ok:
			res = res = requests.put(endpoint, data=payload, headers=headers)
			if res.ok:
				json_res = res.json()
				print(json_res)
			else:
				return False

		else:
			return False'''

	def test_read_existing_key(self):
		pass

	def test_remove_existing_key(self):
		pass


	# more advanded tests
	# -------------------------------------------------------------------------
	'''def test_view_change(self):
		view = [addr1, addr2, addr3, addr4, addr5]
		endpoint = 'http://127.0.0.1:13802/kv-store/view-change'
		headers = {'content-type': 'application/json'}
		payload = json.dumps({'view': view, 'repl_factor': 2, 'causal-context': {}})

		print(endpoint)
		print(payload)


		res = requests.put(endpoint, data=None, headers=headers)
		if res.ok:
			json_res = res.json()
			print(json_res)
		else:
			print(res)
			return False'''

	def test_single_node_failure(self):
		pass

	def test_multi_node_failure(self):
		pass

	def test_network_partition(self):
		pass


# execution starts here
# -----------------------------------------------------------------------------
if __name__ == '__main__':
	unittest.main()





