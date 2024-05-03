#!/usr/bin/env bash

set -eu

if [[ $# != 2 ]]; then
    echo "Usage: $0 <seed url> <path to result>"
    exit 1
fi

seed_url=$1
path_to_result=$2

# TODO: actual implementation should go here
python3 -m venv venv
. venv/bin/activate


python3 ./main.py $seed_url $path_to_result

echo "Finished running"
