import asyncio
import csv
import os
import subprocess
import glob
from quart import Quart, render_template, jsonify
from quart_cors import cors

app = Quart(__name__)
app = cors(app, allow_origin="*")

INTERFACE = 'wlan1'
CSV_PREFIX = '/dev/shm/scan'
TARGET_MAC = None

def get_latest_csv():
    files = glob.glob(f"{CSV_PREFIX}-*.csv")
    if not files:
        return None
    return max(files, key=os.path.getmtime)

def parse_csv():
    devices = []
    current_file = get_latest_csv()
    
    if not current_file or not os.path.exists(current_file):
        return []
    
    try:
        with open(current_file, 'r', newline='', errors='ignore') as f:
            content = f.read().split('\n\n')[0]
            lines = content.splitlines()
            if len(lines) < 2: return []
            
            reader = csv.DictReader(lines[1:])
            for row in reader:
                data = {k.strip(): v.strip() for k, v in row.items()}
                if 'BSSID' in data and data.get('Power') and data['Power'] != '-1':
                    devices.append({
                        "MAC": data['BSSID'],
                        "Power": int(data['Power']),
                        "Channel": data['channel'],
                        "Name": data['ESSID'] or "Unknown"
                    })
    except:
        pass
    return devices

def run_airodump(ch=None, bssid=None):
    subprocess.run(["sudo", "pkill", "airodump-ng"])
    
    for f in glob.glob(f"{CSV_PREFIX}*"):
        try: os.remove(f)
        except: pass

    cmd = [
        "sudo", "airodump-ng", INTERFACE,
        "-w", CSV_PREFIX,
        "--output-format", "csv",
        "--write-interval", "1"
    ]
    
    if ch and bssid:
        cmd.extend(["-c", ch, "--bssid", bssid])

    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

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
    
    return jsonify(sorted(all_devices, key=lambda x: x['Power'], reverse=True)[:5])

@app.route('/start_target/<ch>/<mac>')
async def start_target(ch, mac):
    global TARGET_MAC
    TARGET_MAC = mac.upper()
    run_airodump(ch, mac)
    return jsonify({"status": "tracking", "mac": mac})

@app.route('/stop_target')
async def stop_target():
    global TARGET_MAC
    TARGET_MAC = None
    run_airodump()
    return jsonify({"status": "resumed_general_scan"})

@app.route('/health')
async def health():
    check = subprocess.run(["pgrep", "airodump-ng"], capture_output=True)
    if not check.stdout:
        run_airodump()
        return jsonify({"status": "restarting"})
    return jsonify({"status": "ok"})

@app.before_serving
async def startup():
    run_airodump()

@app.route('/exit_kiosk')
async def exit_kiosk():
    # kill chromium and the python server
    subprocess.Popen(["sudo", "pkill", "chromium"])
    # optional: restart networking if you want internet back immediately
    subprocess.Popen(["sudo", "systemctl", "start", "NetworkManager"])
    return jsonify({"status": "exiting"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)