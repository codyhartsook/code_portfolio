from datetime import datetime
from flask import jsonify
import sys
import json

class KV_store():

    def __init__(self, IPAddress):
        self.history = [("Initialized", datetime.now())]
        self.keystore = {}
        self.IPAddress = IPAddress

    """
        Functions below only read from the database
    """

    def containsKey(self, key):
        '''
        Returns the True if the key is contained in the local database
        '''
        return (key in self.keystore)

    def numberOfKeys(self):
        '''
        Returns the number of keys in the local database
        '''
        return len(self.keystore)

    def printHistory(self):
        '''
        Prints all events which have occured on this database
        '''
        for event in self.history:
            print(event[0] + ": " + event[1].strftime("%m/%d/%Y, %H:%M:%S"))

    def returnHistory(self):
        '''
        Prints all events which have occured on this database
        '''
        output = "<center>"
        for event in self.history:
            output = output + event[0] + ": " + event[1].strftime("%m/%d/%Y, %H:%M:%S") + "<br>"
        return output + "</center>"

    def insertKey(self, key, value, context, address=None):
        response = {}
        code = 0
        response["causal-context"] = context
        if address is not None:
            response["address"] = address
        if (value is None):
            response["message"] = "Error in PUT"
            response["error"] = "Value is missing"
            code = 400
        elif (len(value) > 50):
            response["message"] = "Error in PUT"
            response["error"] = "Value is too long"
            code = 400
        elif (self.containsKey(key)):
            self.keystore[key] = value
            response["message"] = "Updated successfully"
            response["replaced"] = True
            code = 200
        else:
            self.keystore[key] = value
            response["replaced"] = False
            response["message"] = "Added successfully"
            code = 200
        return json.dumps(response), code

    def removeKey(self, key, context, address=None):
        response = {}
        code = 0
        response["causal-context"] = context
        if address is not None:
            response["address"] = address
        if self.containsKey(key):
            del self.keystore[key]
            response["message"] = "Deleted successfully"
            response["doesExist"] = True
            code = 200
        else:
            response["message"] = "Error in DELETE"
            response["error"]   = "Key does not exist"
            response["doesExist"]= False
            code = 404
        return json.dumps(response), code

    def readKey(self, key, context, address=None):
        response = {}
        code = 0
        response["causal-context"] = context
        if address is not None:
            response["address"] = address
        if self.containsKey(key):
            response["message"] = "Retrieved successfully"
            response["doesExist"] = True
            response["value"]   = self.keystore[key]
            code = 200
        else:
            response["message"] = "Error in GET"
            response["error"]   = "Key does not exist"
            response["doesExist"]= False
            code = 404
        return json.dumps(response), code