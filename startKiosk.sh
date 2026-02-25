#!/bin/bash

# kill old processes
sudo pkill -f macSearchAPI.py
sudo pkill airodump-ng
sudo pkill chromium

# stop interference and start monitor mode
sudo airmon-ng check kill
sudo airmon-ng start wlan1

# wait for hardware
sleep 2

# force interface up
if ip link show wlan1mon > /dev/null 2>&1; then
    sudo ip link set wlan1mon up
    interface="wlan1mon"
else
    sudo ip link set wlan1 up
    interface="wlan1"
fi

# clear old scan data from ram
sudo rm -rf /dev/shm/scan*

# launch server in background
echo "starting auditor on $interface"
sudo python3 macSearchAPI.py &

# wait for server to warm up
sleep 5

# tell chromium which screen to use
export DISPLAY=:0

# launch chromium as the pi user to avoid sandbox/root errors
sudo -u pi chromium-browser --kiosk --noerrdialogs --disable-infobars http://localhost:5000 &