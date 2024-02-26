#!/usr/bin/env bash

set -eu

# TODO: place real preparations for your parser here

python3.8 -m venv venv
. venv/bin/activate

which python

pip install -r requirements.txt

cd venv/lib/python3.8/site-packages
ls