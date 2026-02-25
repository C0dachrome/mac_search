import asyncio
import csv
import os
import subprocess
from quart import Quart, render_template, jsonify
from quart_cors import cors

app = Quart(__name__)
app = cors(app, allow_origin="*")

INTERFACE = 'wlan1'
CSV_FILE = '/dev/shm/scan-01.csv'

TARGET_MAC = None

def parse_csv():
    devices = []
    if not os.path.exists(CSV_FILE):
        return []
    
    try:
        # 'rU' or newline='' helps handle files that are being written to
        with open(CSV_FILE, 'r', newline='', errors='ignore') as f:
            content = f.read().split('\n\n')[0]
            lines = content.splitlines()
            if len(lines) < 2: return []
            
            reader = csv.DictReader(lines[1:])
            for row in reader:
                data = {k.strip(): v.strip() for k, v in row.items()}
                if 'BSSID' in data and data['Power'] != '-1':
                    devices.append({
                        "MAC": data['BSSID'],
                        "Power": int(data['Power']),
                        "Channel": data['channel'],
                        "Name": data['ESSID'] or "Unknown"
                    })
    except Exception as e:
        print(f"Read error: {e}")
    return devices

# Add a check to ensure airodump hasn't died
@app.route('/health')
async def health():
    # Check if airodump-ng is in the process list
    check = subprocess.run(["pgrep", "airodump-ng"], capture_output=True)
    if not check.stdout:
        start_general_scan() # Restart it if it died
        return jsonify({"status": "restarting"})
    return jsonify({"status": "ok"})

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/get_data')
async def get_data():
    global TARGET_MAC
    all_devices = parse_csv()
    
    if TARGET_MAC:
        match = [d for d in all_devices if d['MAC'].upper() == TARGET_MAC]
        if match:
            match[0]['IsTarget'] = True
            return jsonify([match[0]])

    sorted_devices = sorted(all_devices, key=lambda x: x['Power'], reverse=True)[:5]
    return jsonify(sorted_devices)

@app.route('/start_target/<ch>/<mac>')
async def start_target(ch, mac):
    global TARGET_MAC
    TARGET_MAC = mac.upper()

    subprocess.run(["sudo", "pkill", "airodump-ng"])
    cmd = [
        "sudo", 
        "airodump-ng", 
        INTERFACE, 
        "-c", 
        ch, 
        "--bssid", 
        mac, 
        "-w", 
        "/dev/shm/scan", 
        "--output-format", 
        "csv", 
        "--write-interval", 
        "1"
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return jsonify({"status": "tracking", "mac": mac})

def start_general_scan():
    subprocess.run(["sudo", "pkill", "airodump-ng"])

    cmd = [
        "sudo", "airodump-ng", INTERFACE, 
        "-w", "/dev/shm/scan", 
        "--output-format", "csv", 
        "--write-interval", "1",
        "--background" 
    ]

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@app.route('/stop_target')
async def stop_target():
    global TARGET_MAC
    TARGET_MAC = None
    start_general_scan()
    return jsonify({"status": "resumed_general_scan"})

@app.before_serving
async def startup():
    if os.path.exists('/dev/shm/scan-01.csv'):
        os.remove('/dev/shm/scan-01.csv')
    start_general_scan()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)