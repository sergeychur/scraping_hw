#!/usr/bin/env bash

set -eu

mkdir ./real_results/
echo "Running parser implementation "
cur_user=$(whoami)
timeout 1200 ./scripts/run.sh http://localhost/wiki/Чемпионат_Европы_по_футболу_2024 ./real_results/result.jsonl
echo "Assessing results"
venv/bin/python ./scripts/compare_results.py ./test_data/result.jsonl ./real_results/result.jsonl
echo "OK"
