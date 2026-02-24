#!/bin/bash

interface="wlan1"

read -p "Delete all scan-*.csv files? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -f scan-[0-9]*.csv
fi

sudo airodump-ng -w scan --write-interval 1 --output-format csv "$interface"

# Run Python and forward interrupts to it so Ctrl-C stops Python but keeps
# this wrapper running. A second Ctrl-C will terminate the wrapper.
python macSearch.py 

interrupted=0
trap_handler() {
    if kill -0 "$child" 2>/dev/null; then
        echo
        echo "Interrupting Python (PID $child)..."
        kill -INT "$child" 2>/dev/null || true
        interrupted=1
    else
        if [[ $interrupted -eq 1 ]]; then
            echo
            echo "Interrupted again — exiting wrapper."
            trap - INT TERM
            kill -INT $$ 2>/dev/null || exit 1
        else
            echo
            echo "Python not running. Continuing..."
            interrupted=1
        fi
    fi
}
trap 'trap_handler' INT TERM



# Restore default handlers so further Ctrl-C behaves normally.
trap - INT TERM

# Ask for the parameters after Python finishes (or is interrupted).
read -p "Enter channel: " channel
read -p "Enter target MAC address (BSSID): " MAC_ADDRESS

echo "Starting targeted airodump-ng with channel=$channel, bssid=$MAC_ADDRESS, interface=$interface"
sudo airodump-ng -c "$channel" --bssid "$MAC_ADDRESS" -w target --write-interval 1 "$interface"

