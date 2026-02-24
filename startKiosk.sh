#!/bin/bash
# 1. Kill everything first
sudo killall -9 python3 airodump-ng xinit 2>/dev/null

# 2. Delete ALL old scans so airodump is forced to use 'scan-01.csv'
rm -f /home/codyc/mac_search/scan-*

# 3. Put the card in Monitor Mode (Crucial for Power levels)
sudo ifconfig wlan1 down
sudo iw dev wlan1 set type monitor
sudo ifconfig wlan1 up

# 4. Start fresh scan
sudo airodump-ng -w /home/codyc/mac_search/scan --write-interval 1 --output-format csv wlan1 > /dev/null 2>&1 &

# 5. Start API
python3 /home/codyc/mac_search/macSearchAPI.py > /home/codyc/api.log 2>&1 &

# 6. Wait for file to actually exist before launching browser
while [ ! -f /home/codyc/mac_search/scan-01.csv ]; do
  sleep 1
done

# 7. Launch Browser
xinit /usr/bin/chromium --kiosk --no-sandbox --app=http://localhost:5000