from flask import Flask, request, jsonify, make_response
import json
import os
import requests
import time
import sys

'''
Defines routing methods including GET, PUT, DELETE, and a general FORWARD
Defines causal objects and provides parsing methods
'''

max_wait = 5

class Router():
	def __init__(self):
		self.methods = ['GET', 'POST', 'DELETE']
		self.max_wait = 5
		self.error_message = 'Timeout'

	# -------------------------------------------------------------------------
	def base(self, address, path):
		endpoint = 'http://' + address + path
		print(endpoint, file=sys.stderr)
		headers = {'content-type': 'application/json'}
		return endpoint, headers

	# -------------------------------------------------------------------------
	def GET(self, address, path, data):
		
		endpoint, header = self.base(address, path)

		r = requests.get(endpoint, json=data, headers=header, timeout=max_wait)

		return r


	# -------------------------------------------------------------------------
	def PUT(self, address, path, data):
		
		endpoint, header = self.base(address, path)

		r = requests.put(endpoint, json=data, headers=header, timeout=max_wait)
		return r

	# -------------------------------------------------------------------------
	def DELETE(self, address, path, data):
		
		endpoint, header = self.base(address, path)

		r = requests.delete(endpoint, json=data, headers=header, timeout=max_wait)

		return r

	# -------------------------------------------------------------------------
	def FORWARD(self, address, method, path, data):
		if method == "GET":
			return self.GET(address,path,data)
		if method == "PUT":
			return self.PUT(address,path,data)
		if method == "DELETE":
			return self.DELETE(address,path,data)





