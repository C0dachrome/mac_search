#!/bin/bash

# kill old processes
sudo pkill -f macSearchAPI.py
sudo pkill airodump-ng
sudo pkill chromium

# stop interference (this kills your internet)
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

# launch chromium
export DISPLAY=:0
sudo -u codyc chromium --kiosk --noerrdialogs --disable-infobars http://localhost:5000 &

# keep the script alive until you press ctrl+c
echo "auditor is running. press ctrl+c to stop and restore internet."
trap "sudo systemctl start NetworkManager; sudo airmon-ng stop $interface; exit" INT
wait