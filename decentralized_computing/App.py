# test environment


# simulate functionality for end users
# this would require sign in and authentication
from system_core import Client, Compute_Engine

def Def_Role():
	print("to sign up as a network server press S")
	print("to utilize the cloud computing network press C")

	role = input()

	if role == "S" or role == "s":
		server = Compute_Engine()
		server.network_server_connection()

	elif role == "C" or role == "c":
		client = Client()
		client.network_server_connection()

	else:
		Def_Role()

# spam network with compute engine regestry
def build_network():
	for server in range(10):
		server = Compute_Engine()
		server.network_server_connection()

if __name__ == "__main__":

	build_network()

	while True:
		try:
			Def_Role()
		except:
			print("\ndone")
			break

