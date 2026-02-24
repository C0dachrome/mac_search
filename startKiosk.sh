#!/bin/bash
interface="wlan1"

# 1. Reset wireless
sudo rfkill unblock all
sudo ifconfig "$interface" up

# 2. Kill old sessions
sudo killall python3 airodump-ng xinit 2>/dev/null

# 3. Start Airodump (Background)
sudo airodump-ng -w scan --write-interval 1 --output-format csv "$interface" > /dev/null 2>&1 &

# 4. Start Python API (Background)
# Make sure the path to your script is correct!
python3 /home/codyc/mac_search/macSearchAPI.py > /home/codyc/api.log 2>&1 &

# 5. THE FAILSAFE: Wait until the port is active
echo "Waiting for Python API to wake up..."
while ! nc -z localhost 5000; do   
  sleep 0.5
done
echo "API is live! Launching browser..."

# 6. Launch Graphics
xinit /usr/bin/chromium --kiosk --no-sandbox --app=http://localhost:5000 --user-data-dir=/home/codyc/.chrome-kiosk