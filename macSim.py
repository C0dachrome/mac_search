import time
import random

def update_mock_csv(power_val):
    content = f"""BSSID, First time enabled, Last time enabled, channel, Speed, Privacy, Cipher, Authentication, Power, # beacons, # IV, LAN IP, ID-length, ESSID, Key
 00:11:22:33:44:55, 2023-10-27 10:00:00, 2023-10-27 10:00:05,  6,  54, WPA2, CCMP, PSK, {power_val}, 100, 0, 0.0.0.0, 5, Dolby_Speaker, 

Station MAC, First time enabled, Last time enabled, Power, # packets, BSSID, Probed ESSIDs
 AA:BB:CC:DD:EE:FF, 2023-10-27 10:00:01, 2023-10-27 10:00:06, {power_val - 10}, 25, 00:11:22:33:44:55, 
"""
    with open('scan-01.csv', 'w') as f:
        f.write(content)

# Start at -80 (far away) and get closer to -30 (hot)
p = -80
while p < -20:
    update_mock_csv(p)
    print(f"Simulating signal at {p} dBm...")
    p += 2  # Getting closer!
    time.sleep(1)
