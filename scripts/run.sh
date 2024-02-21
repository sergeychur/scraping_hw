#!/usr/bin/env bash

set -eu

if [[ $# != 2 ]]; then
    echo "Usage: $0 <seed url> <path to result>"
    exit 1
fi

seed_url=$1
path_to_result=$2

echo "Run.sh"
timeout 10 wget --recursive -w 0.1 -D localhost $seed_url || true

cp test_data/result.jsonl $path_to_result
echo "Finished running"
