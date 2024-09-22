#!/usr/bin/env bash

set -eu

# TODO: place real preparations for your parser here

python3.12 -m venv venv
. venv/bin/activate

pip install -r requirements.txt
