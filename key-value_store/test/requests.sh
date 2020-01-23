# ------------------------------
# heredoc strings of example requests
# for info on heredoc strings:
#   http://www.guguncube.com/2140/unix-set-a-multi-line-text-to-a-string-variable-or-file-in-bash

read -d '' sample_view << "VIEW_STR"
{
    "view": [
        "10.10.0.2:13800",
        "10.10.0.3:13800",
        "10.10.0.4:13800",
        "10.10.0.5:13800"
    ],
    "repl-factor": 2
}
VIEW_STR

# NOTE: need to sub ${sample_view} in another way
read -d '' view_change_template <<"VIEW_CHANGE_STR"
curl -s --request   PUT
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      ${sample_view}
        http://localhost:13802/kv-store/view-change
VIEW_CHANGE_STR

# ------------------------------
# Metadata operations

read -d '' key_count_template <<"KEY_COUNT_STR"
curl -s --request   GET
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      '{"causal-context": {}}'
        http://localhost:13802/kv-store/key-count
KEY_COUNT_STR

read -d '' get_all_shards_template <<"ALL_SHARDS_STR"
curl -s --request   GET
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      '{"causal-context": {}}'
        http://localhost:13802/kv-store/shards
ALL_SHARDS_STR

read -d '' get_shard_template <<"SHARD_INFO_STR"
curl -s --request   GET
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      '{"causal-context": {}}'
        http://localhost:13802/kv-store/shards/id
SHARD_INFO_STR

# ------------------------------
# Key operations

read -d '' get_key_template <<"GET_KEY_STR"
curl -s --request   GET
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      '{"causal-context": {}}'
        http://localhost:13802/kv-store/keys/sampleKey
GET_KEY_STR

read -d '' put_key_template <<"PUT_KEY_STR"
curl -s --request   PUT
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      '{"value": "sampleValue", "causal-context": {}}'
        http://localhost:13802/kv-store/keys/sampleKey
PUT_KEY_STR

read -d '' del_key_template <<"DEL_KEY_STR"
curl -s --request   DELETE
        --header    "Content-Type: application/json"
        --write-out "\n%{http_code}\n"
        --data      '{"causal-context": {}}'
        http://localhost:13802/kv-store/keys/sampleKey
DEL_KEY_STR


# ------------------------------
# Main

# print out the above strings for convenience
echo "Sample requests:"

echo ${key_count_template}
echo ${view_change_template}
echo ${get_key_template}
echo ${put_key_template}
echo ${del_key_template}
