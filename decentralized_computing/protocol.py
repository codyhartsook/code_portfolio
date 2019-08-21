# -----------------------------------------------------------------------------
# protocol for client server connections
# establish argreed upon messages
# -----------------------------------------------------------------------------

# if a client or server does not send the correct initial message, send nak
def handle_message(message):
	if message[0] not in valid_requests:
		return NAK()
	else:
		msg = valid_requests[message[0]]() # call function associated with message
		return msg

def handle_obj(obj_var):
	pass

def client_to_network():
	return "client"

def compute_to_network():
	return "engine"

def client_to_compute():
	return "compute"

def ACK():
	return True

def NAK():
	return False

valid_requests = {
	"ack":ACK, 
	"nak":NAK, 
	"register_comp":compute_to_network, 
	"client_connect":client_to_network,
	"peer_connection":client_to_compute
	}

