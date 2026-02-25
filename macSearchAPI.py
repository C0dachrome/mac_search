import asyncio
from quart import Quart, render_template, jsonify
from quart_cors import cors
from pyrcrack import AirodumpNg

app = Quart(__name__)
app = cors(app, allow_origin="*")

INTERFACE = 'wlan1'
air = AirodumpNg()
TARGET_MAC = None

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/get_data')
async def get_data():
    global TARGET_MAC
    try:
        results = air.get_count()
        devices = []
        
        if TARGET_MAC:
            for ap in results:
                if ap.bssid.upper() == TARGET_MAC:
                    return jsonify([{
                        "MAC": ap.bssid,
                        "Power": ap.dbm,
                        "Channel": ap.channel,
                        "Name": ap.essid or "Unknown",
                        "IsTarget": True
                    }])

        for ap in results:
            devices.append({
                "MAC": ap.bssid,
                "Power": ap.dbm,
                "Channel": ap.channel,
                "Name": ap.essid or "Unknown"
            })
        
        return jsonify(sorted(devices, key=lambda x: x['Power'], reverse=True)[:5])
    except:
        return jsonify([])

@app.route('/start_target/<ch>/<mac>')
async def start_target(ch, mac):
    global TARGET_MAC
    TARGET_MAC = mac.upper()
    return jsonify({"status": "tracking", "mac": mac})

async def run_scanner():
    async with air(INTERFACE) as scanner:
        while True:
            await asyncio.sleep(1)

@app.before_serving
async def startup():
    app.add_background_task(run_scanner)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)