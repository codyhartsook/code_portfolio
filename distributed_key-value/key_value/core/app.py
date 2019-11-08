# listen to requests clients and internal shards

from flask import Flask, request, jsonify, make_response
import json
import os
import requests

# import shard class
from shard import Partition

app = Flask(__name__)
@app.route("/")
def root():
	return "Home: CS 138: Assignment 3"

# get/put/delete key for shard
@app.route("/kv-store/keys/<keyName>", methods=["GET", "PUT", "DELETE"])
def update_keys(keyName):

	return jsonify({
				"hit"     : "you pinged me",
				"message"   : "update_keys endpoint"
		}), 200

	# get the shard that is storing this key, or new shard
	"""key_shard = '10.10.0.3:13800' #shard.key_op(keyName)

	op = request.method
	data = request.get_json()

	# we have the key locally
	if (key_shard.IP == shard.IP):
		return exec_op(op, data)

	else:
	path = '/kv-store/keys/'+keyName
	return forward(key_shard, path, op, data)"""

# get number of keys in system
@app.route("/kv-store/key-count", methods=["GET"])
def get_key_count():
	# call shard.key_count()
	pass

# change our current view, repartition keys
@app.route("/kv-store/view-change", methods=["PUT"])
def new_view():
	# call shard.view_change(new_view)
	pass

# forward 
def forward(ADDRESS, path, method, data):

	ip_port = ADDRESS.split(":")
	endpoint = 'http://' + ip_port[0] + ":" + ip_port[1] + path
	headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
			
	# make recursive type call but to different ip
	if method == "PUT":
		r = requests.put(endpoint, data=data, headers=headers)
		return make_response(r.content, r.status_code)
	elif method == "GET":
		r = requests.get(endpoint, data=data, headers=headers)
		return make_response(r.content, r.status_code)
	elif method == "DELETE":
		r = requests.delete(endpoint, data=data, headers=headers)
		return make_response(r.content, r.status_code)
	else:
		return jsonify({
				"error"     : "invalid requests method",
				"message"   : "Error in forward"
		}), 400

def exec_op(method, data):
	pass

# run the servers
if __name__ == "__main__":

	# exract view and ip
	VIEW_STR = os.environ["VIEW"]
	views = VIEW_STR.split(",")
	ADDRESS = os.environ["ADDRESS"]

	# create initial shard for this node, hash this shard
	shard = Partition(ADDRESS, views)

	app.run(host='0.0.0.0', port=13800, debug=True)






