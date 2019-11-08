docker stop node1

docker rm node1

docker build -t kv-store:3.0 .

# example node addresses
addr1="10.10.0.2:13800"
addr2="10.10.0.3:13800"
addr3="10.10.0.4:13800"

# convenience variables
initial_full_view="${addr1},${addr2}"
full_view=${initial_full_view},${addr3}

docker run -p 13802:13800 \
		--net=kv_subnet \
		--ip=10.10.0.2 \
		--name="node1" \
		-e ADDRESS="${addr1}" \
		-e VIEW=${initial_full_view} \
		kv-store:3.0


