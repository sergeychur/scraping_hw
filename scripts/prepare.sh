#!/usr/bin/env bash

set -eu

# TODO: place real preparations for your parser here

python3.8 -m venv venv
. venv/bin/activate
ls

pip install -r requirements.txt

cd venv
ls