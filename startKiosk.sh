#!/bin/bash

# kill old processes
sudo pkill -f macSearchAPI.py
sudo pkill airodump-ng

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

# launch server
echo "starting auditor on $interface"
sudo python3 macSearchAPI.py