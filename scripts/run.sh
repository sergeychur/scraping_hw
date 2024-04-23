#!/usr/bin/env bash

set -eu

if [[ $# != 2 ]]; then
    echo "Usage: $0 <seed url> <path to result>"
    exit 1
fi

which python

seed_url=$1
path_to_result=$2

# TODO: actual implementation should go here
timeout 10 wget --recursive -w 0.1 -D localhost $seed_url || true

python3 ./main.py $seed_url ./test_data/result.jsonl

cp ./test_data/result.jsonl $path_to_result
echo "Finished running"
