#!/usr/bin/env bash

set -eu

if [[ $# != 1 ]]; then
    echo "Usage: $0 <path to local folder>"
    exit 1
fi

local_folder=$1

mkdir ./real_results/
echo "Running parser implementation "
cur_user=$(whoami)
timeout --verbose 120 ./scripts/run.sh http://localhost/wiki/Чемпионат_Европы_по_футболу_2024 ./real_results/result.jsonl
echo "Assessing results"
python ./scripts/compare_results.py ${local_folder}/result.jsonl ./real_results/result.jsonl
echo "OK"
