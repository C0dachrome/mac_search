#!/bin/bash

read -p "Delete all scan-*.csv files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f scan-[0-9]*.csv
fi

sudo airodump-ng -w scan --write-interval 1 --output-format csv wlan1

python macSearch.py

