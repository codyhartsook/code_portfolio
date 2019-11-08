from flask import Flask, request, jsonify, make_response
import json
from Database import Database
import os
import requests

database = Database()

app = Flask(__name__)

@app.route("/")
def root():
	return "Home: CS 138: Assignment 3"

@app.route("/kv-store/keys/<keyName>", methods=["GET", "PUT", "DELETE"])
def kvstore(keyName):
	'''
		The main Key-Value store endpoint

		: GET		-> return the value for the key
		: PUT		-> add or update a key
		: DELETE	-> delete a key
	'''
	if (request.method == "GET"):
		return database.readKey(keyName)
	elif (request.method == "PUT"):
		data = request.get_json()
		return database.insertKey(keyName, data.get("value"))
	elif (request.method == "DELETE"):
		return database.removeKey(keyName)
	else:
		return jsonify({
			"error"		: "somethings not right"
		}), 400




# run the servers
if __name__ == "__main__":
	# run it on our localhost with a port of 8081 with debugging enabled so we can auto restart when changes are made
	app.run(host='0.0.0.0', port=13800, debug=True)




