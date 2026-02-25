import asyncio
from quart import Quart, render_template, jsonify
from pyrcrack import AirodumpNg

app = Quart(__name__)
air = AirodumpNg()
INTERFACE = 'wlan1'

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/get_data')
async def get_data():
    devices = []
    for ap in air.get_count():
        devices.append({
            "MAC": ap.bssid,
            "Power": ap.dbm,
            "Channel": ap.channel,
            "Name": ap.essid or "Unknown AP"
        })
    
    sorted_devices = sorted(devices, key=lambda x: x['Power'], reverse=True)[:5]
    return jsonify(sorted_devices)

async def start_airodump():
    async with air(INTERFACE) as scanner:
        while True:
            await asyncio.sleep(1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(start_airodump())
    app.run(host='0.0.0.0', port=5000)