#!/bin/bash

interface="wlan1"
sudo rfkill unblock all
sleep 1
sudo ifconfig "$interface" up

rm -f /home/codyc/mac_search/scan-*.csv

python3 /home/codyc/mac_search/macSearchAPI.py > /home/codyc/api.log 2>&1 &

sudo airodump-ng -w scan --write-interval 1 --output-format csv "$interface" > /dev/null 2>&1 &

sleep 3

xinit /usr/bin/chromium --kiosk --incognito --no-sandbox --app=http://localhost:5000 --user-data-dir=/home/codyc/.chrome-kiosk --nocursor