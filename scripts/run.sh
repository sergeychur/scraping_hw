#!/usr/bin/env bash

set -eu

if [[ $# != 2 ]]; then
    echo "Usage: $0 <seed url> <path to result>"
    exit 1
fi

seed_url=$1
path_to_result=$2

venv/bin/python scraper/main.py $seed_url $path_to_result

timeout 10 wget --recursive -w 0.1 -D localhost $seed_url || true

echo "Finished running"
