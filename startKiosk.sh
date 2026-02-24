#!/bin/bash

interface="wlan1"
sudo rfkill unblock all
sleep 1
sudo ifconfig "$interface" up

# Start the Python API in the background
python3 /home/codyc/mac_search/macSearchAPI.py > /home/codyc/api.log 2>&1 &

sudo airodump-ng -w scan --write-interval 1 --output-format csv "$interface" &

sleep 3

# Launch the browser in fullscreen directed at the API
xinit /usr/bin/chromium --kiosk --incognito--app=http://localhost:5000 --user-data-dir=/home/codyc/.chrome-kiosk