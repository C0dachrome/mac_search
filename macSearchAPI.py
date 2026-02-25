import asyncio
import csv
import os
import subprocess
from quart import Quart, render_template, jsonify
from quart_cors import cors

app = Quart(__name__)
app = cors(app, allow_origin="*")

INTERFACE = 'wlan1'
CSV_FILE = '/tmp/scan-01.csv'
TARGET_MAC = None

def parse_csv():
    devices = []
    if not os.path.exists(CSV_FILE):
        return []
    
    try:
        with open(CSV_FILE, 'r') as f:
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
        print(f"Parse error: {e}")
        
    return devices

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
    return jsonify({"status": "tracking", "mac": mac})

@app.before_serving
async def startup():
    if os.path.exists('/tmp/scan-01.csv'):
        os.remove('/tmp/scan-01.csv')
    
    cmd = ["sudo", "airodump-ng", INTERFACE, "-w", "/tmp/scan", "--output-format", "csv"]
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)