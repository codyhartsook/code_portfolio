'''
app.py defines the network nodes that listen to requests from
clients and other nodes int the system.
'''

from flask import Flask, request, jsonify, make_response, g
import json
import os
import requests
from node import Node
from Message import Router
import sys
from vectorclock import VectorClock
import random

app = Flask(__name__)

@app.route('/')
def root():
	return "root"

'''
get the current state of this node
'''
@app.route('/kv-store/state', methods=['GET'])
def state():
	
	return jsonify({
				'node state:'     : shard.__repr__()
	}), 200

'''
all production/public endpoints
---------------------------------------------------------------------------------
'''

'''
get number of keys for a node and stored replicas
'''
@app.route('/kv-store/key-count', methods=['GET'])
def get_key_count():
	response = {
		"message"       : "Key count retrieved successfully",
        "key-count"     : shard.numberOfKeys(),
        "shard-id"      : shard.shard_ID,
        "causal-context": shard.VC.__repr__()
	}
	return json.dumps({"key-count" : response}), 200

'''
get shard ID and key count for each shard
'''
@app.route('/kv-store/shards', defaults={'ID': None}, methods=['GET'])
@app.route('/kv-store/shards/<ID>', methods=['GET'])
def shards(ID):

	if ID:
		ID = int(ID)
		response = {}
		response['get-shard'] = {}
		response['get-shard']['message'] = 'Shard information retrieved successfully'
		response['get-shard']['shard-id'] = ID
		response['get-shard']['causal-context'] = {} #shard.VC.returnClock()
		response['get-shard']['replicas'] = shard.shard_replicas(ID)

		return json.dumps(response), 200

	else:
		response = {}
		response['shard-membership'] = {}
		response['shard-membership']['message'] = 'Shard membership retrieved successfully'
		response['shard-membership']['causal-context'] = shard.VC.__repr__()
		response['shard-membership']['shards'] = []

		for shard_ID in range(len(shard.P_SHARDS)):
			response['shard-membership']['shards'].append(shard_ID)

		return json.dumps(response), 200

'''
Change our current view and re-shard keys
Before we re-shard, make sure new node is up 
'''
@app.route('/kv-store/view-change', methods=['PUT'])
def new_view():

	data = request.get_json()
	view = data.get('view')
	repl_factor = data.get('repl-factor')

	print('new view', view, file=sys.stderr)

	path = '/kv-store/internal/view-change'
	all_nodes = shard.all_nodes()

	for node in all_nodes:
		shard.VC.appendShard(node)
		if node == shard.ADDRESS:
			continue
		try:
			res = router.PUT(node, path, data)
		except:
			print('error occured in view change', file=sys.stderr)
			continue

	print('made if past forwarding view_change', file=sys.stderr)

	shard.view_change(view, repl_factor)

	print('made if past my view_change', file=sys.stderr)

	response = {}
	response['view-change'] = {}
	response['view-change']['message'] = 'View change successful'
	response['view-change']['causal-context'] = shard.VC.returnClock()
	response['view-change']['shards'] = []

	for shard_ID in range(len(shard.P_SHARDS)):
		response['view-change']['shards'].append({'shard-id':shard_ID, 'replicas':shard.P_SHARDS[shard_ID]})

	return json.dumps(response), 200

'''
get/put/delete key for shard
'''
@app.route('/kv-store/keys/<keyName>', defaults={'forward': None}, methods=['GET', 'PUT', 'DELETE'])
@app.route('/kv-store/keys/<keyName>/<forward>', methods=['GET', 'PUT', 'DELETE'])
def update_keys(keyName, forward):
	print(shard.P_SHARDS, file=sys.stderr)
	# find the shard that is associated with this key
	key_shard = shard.find_match(keyName)
	print('sending', keyName, 'to shard', key_shard, file=sys.stderr)
	all_replicas = shard.shard_replicas(key_shard)
	# we have the key locally
	data = request.get_json()
	read_permissions = True
	write_permissions = True
	if data is not None:
		if "causal-context" in data:
			read_permissions = shard.VC.allowRead(data["causal-context"],ADDRESS)
			write_permissions = shard.VC.allowWrite(data["causal-context"],ADDRESS)	
	if (key_shard == shard.shard_ID):
		method = request.method
		if method == 'PUT':
			if not write_permissions:
				return jsonify({"error":"Unable to satisfy request","message":"Error in PUT","causal-context": shard.VC.__repr__()}), 503
			shard.VC.increment(shard.ADDRESS)
			value = data["value"]
			print(data, file=sys.stderr)
			response, code = shard.insertKey(keyName, value, shard.VC.__repr__(), ADDRESS if (forward is not None) else None)
			if (code < 300):
				share_request("PUT", keyName, forward, data)
			return response, code
		elif method == 'GET':
			if not read_permissions:
				return jsonify({"error":"Unable to satisfy request","message":"Error in GET","causal-context": shard.VC.__repr__()}), 503
			return shard.readKey(keyName, shard.VC.__repr__(), ADDRESS if (forward is not None) else None)
		elif method == 'DELETE':
			if not write_permissions:
				return jsonify({"error":"Unable to satisfy request","message":"Error in DELETE","causal-context": shard.VC.__repr__()}), 503
			shard.VC.increment(shard.ADDRESS)
			response, code = shard.removeKey(keyName, shard.VC.__repr__(), ADDRESS if (forward is not None) else None)
			if (code < 300):
				share_request("DELETE", keyName, forward, data)
			return response, code
		else:
			'error occured'
	# forward request to another shard
	else:
		path = '/kv-store/keys/' +keyName + '/forward'
		# forward request to replicas in key_shard shard
		forward_response = None
		forward_code = 0
		random.shuffle(all_replicas)
		for replica in all_replicas:
			if forward_response is None:
				try:
					response = router.FORWARD(replica, request.method, path, request.get_json())
					return json.dumps(response.json()), response.status_code
				except:
					print("error unresponsive", file=sys.stderr)
					shard.handle_unresponsive_node(replica)
					continue
		if forward_response is not None:
			return forward_response, forward_code
		else:
			# we have gone through all replicas and none have responded
			if request.method == 'PUT':
				return jsonify({"error":"Unable to satisfy request","message":"Error in PUT"}), 503
			elif request.method == 'GET':
				return jsonify({"error":"Unable to satisfy request","message":"Error in GET"}), 503
			else:
				return jsonify({"error":"Unable to satisfy request","message":"Error in DELETE"}), 503


def share_request(method, key, forward, data=None):
	if forward == False:

		headers = {'content-type': 'application/json'}
		replicas = shard.shard_replicas(shard.shard_ID)
		random.shuffle(replicas)

		for replica in replicas:
		
			if replica == ADDRESS:
				continue

			print('forwarding to replica:', replica, file=sys.stderr)

			if method == 'DELETE':
				router.DELETE(replica, '/kv-store/keys/' + key + '/forward', data)
			elif method == 'PUT':
				router.PUT(replica, '/kv-store/keys/' + key + '/forward', data)

'''
all internal endpoints
---------------------------------------------------------------------------------
'''

'''
internal shard key count
'''
@app.route('/kv-store/internal/key-count', methods=['PUT'])
def internal_key_count():

	key_count = shard.numberOfKeys()

	return jsonify({
				'key_count'     : key_count,
				'causal-context': shard.VC.__repr__()
	}), 200

'''
get the entire KV store for a given node
'''
@app.route('/kv-store/internal/KV', methods=['GET'])
def get_kv():
	kv_res = json.dumps(shard.keystore)
	return jsonify({
		'KV_Store' : kv_res
		}), 201

'''
internal endpoint for viewchange
'''
@app.route('/kv-store/internal/view-change', methods=['PUT'])
def spread_view():

	data = request.get_json()
	view = data.get('view')
	repl_factor = data.get('repl-factor')
	shard.view_change(view, repl_factor)

	return jsonify({
			'new_view'     : view
	}), 200

@app.route('/kv-store/internal/state-transfer', methods=['PUT'])
def state_transfer():
	data = request.get_json()
	other_vector_clock = data["causal-context"]
	if shard.VC.selfHappensBefore(other_vector_clock):
		shard.keystore = data["kv-store"]
		shard.vc = VectorClock(view=None, clock=other_vector_clock)
	return jsonify({
			"message"	: "Acknowledged"
	}), 201

'''
internal endpoint to gossip/send state to all other replicas
'''

@app.route('/kv-store/internal/gossip/', methods=["PUT"])
def gossip():
	# checks if I am currently gossiping with someone else
	if not shard.gossiping:
		shard.lastToGossip = False
		incoming_data = json.loads(request.get_json())
		shard.gossiping = True
		# causal context of the incoming node trying to gossip
		other_context = incoming_data["causal-context"]
		# key store of incoming node trying to gossip
		other_kvstore = incoming_data["kv-store"]
		# this is true if the other node determined i will be the tiebreaker
		tiebreaker = True if incoming_data["tiebreaker"] == ADDRESS else False
		incoming_Vc = VectorClock(view=None, clock=other_context)
		if other_kvstore == shard.keystore:
			shard.gossiping = False
			return jsonify({
				"message": "We're equal."
			}), 201
		elif incoming_Vc.allFieldsZero():
			shard.gossiping = False
			return jsonify({
				"message" : "You dont have any data"
			}), 201
		elif incoming_Vc.selfHappensBefore(shard.VC.__repr__()):
			# I am at least concurrent or after
			shard.gossiping = False
			return jsonify({
				"message"	: "I Don't need yours."
			}), 201
		elif incoming_Vc.__repr__() != shard.VC.__repr__():
			shard.keystore = other_kvstore
			shard.VC.merge(other_context, ADDRESS)
			shard.gossiping = False
			return jsonify({
				"message" : "I took your data"
			}), 200
	return jsonify({
		"message" : "gossiping"
	}), 201


if __name__ == '__main__':

	# exract view and ip
	VIEW_STR = os.environ['VIEW']
	VIEW = VIEW_STR.split(',')
	ADDRESS = os.environ['ADDRESS']
	REPL_FACTOR = int(os.environ['REPL_FACTOR'])

	# create node and message router
	router = Router()
	shard = Node(router, ADDRESS, VIEW, REPL_FACTOR)

	app.run(host='0.0.0.0', port=13800, debug=False)

