# cp source files to build directory

docker stop node4
docker rm node4

docker build -t kv-store:4.0 .

# example node addresses
addr1="10.10.0.2:13800"
addr2="10.10.0.3:13800"
addr3="10.10.0.4:13800"
addr4="10.10.0.5:13800"

# convenience variables
initial_full_view="${addr1},${addr2}"
full_view=${initial_full_view},${addr3},${addr4}

docker run --name="node4"        --net=kv_subnet     \
           --ip=10.10.0.5        -p 13805:13800      \
           -e ADDRESS="${addr4}"                     \
           -e REPL_FACTOR=2							 \
           -e VIEW=${full_view}                      \
           kv-store:4.0

