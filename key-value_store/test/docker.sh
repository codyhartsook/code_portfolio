# ------------------------------
# Run Docker containers

path_to_dockerfile="This should be a dockerfile path"

docker network create --subnet=10.10.0.0/16 kv_subnet
docker build -t kv-store:4.0 $path_to_dockerfile

# example node addresses
addr1="10.10.0.2:13800"
addr2="10.10.0.3:13800"
addr3="10.10.0.4:13800"
addr4="10.10.0.5:13800"

# convenience variables
initial_full_view="${addr1},${addr2}"
full_view=${initial_full_view},${addr3},${addr4}

read -d '' view_change_data << "VIEW_STR"
{
    "causal-context": {},
    "repl-factor"   : 2,
    "view"          : [
        "10.10.0.2:13800",
        "10.10.0.3:13800",
        "10.10.0.4:13800",
        "10.10.0.5:13800"
    ]
}
VIEW_STR

docker run --name="node1"        --net=kv_subnet     \
           --ip=10.10.0.2        -p 13802:13800      \
           -e ADDRESS="${addr1}"                     \
           -e VIEW=${initial_full_view}              \
           -e REPL_FACTOR=2                          \
           kv-store:4.0

docker run --name="node2"        --net=kv_subnet     \
           --ip=10.10.0.3        -p 13803:13800      \
           -e ADDRESS="${addr2}"                     \
           -e VIEW=${initial_full_view}              \
           -e REPL_FACTOR=2                          \
           kv-store:4.0

# ------------------------------
# add a key

curl --request   PUT                                              \
     --header    "Content-Type: application/json"                 \
     --data      '{"value": "sampleValue", "causal-context": {}}' \
     --write-out "%{http_code}\n"                                 \
     http://${addr2}/kv-store/keys/sampleKey


<<'expected_response'
{
    "message" : "Added successfully",
    "replaced": "false"
}
status code: 201
expected_response


curl --request GET                             \
     --header "Content-Type: application/json" \
     --write-out "%{http_code}\n"              \
     --data      '{"causal-context": {}}'      \
     http://${addr1}/kv-store/keys/sampleKey


<<'expected_response'
{
    "doesExist": "true",
    "message"  : "Retrieved successfully",
    "value"    : "sampleValue",
    "address"  : "10.10.0.3:13800"
}

status code: 200
expected_response


# ------------------------------
# Now we start a new node and add it to the existing store

docker run --name="node3" --net=kv_subnet                          \
           --ip=10.10.0.4  -p 13804:13800                          \
           -e ADDRESS="${addr3}"                                   \
           -e VIEW="${full_view}"                                  \
           -e REPL_FACTOR=2                                        \
           kv-store:4.0

docker run --name="node4" --net=kv_subnet                          \
           --ip=10.10.0.5  -p 13805:13800                          \
           -e ADDRESS="${addr4}"                                   \
           -e VIEW="${full_view}"                                  \
           -e REPL_FACTOR=2                                        \
           kv-store:4.0

curl --request PUT                                                 \
     --header "Content-Type: application/json"                     \
     --data $view_change_data                                      \
     --write-out "%{http_code}\n"                                  \
     http://${addr2}/kv-store/view-change

curl --request GET                                                 \
     --header "Content-Type: application/json"                     \
     --write-out "%{http_code}\n"                                  \
     --data "{\"causal-context\": {}}"                             \
     http://${addr3}/kv-store/keys/sampleKey

<<'expected_response'
{
    "doesExist": "true",
    "message"  : "Retrieved successfully",
    "value"    : "sampleValue",
    "address"  : "10.10.0.2:13800"
}

status code: 200
expected_response
