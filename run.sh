#!/bin/bash

sudo apt install python3-venv python3-tk

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt

python client.py