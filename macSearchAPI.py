from flask import Flask, render_template, jsonify
import pandas as pd
import subprocess
import os

app = Flask(__name__)

CSV_FILE = 'scan-01.csv'
INTERFACE = 'wlan1'

@app.route('/')
def index():
    """Serves the touch-friendly dashboard."""
    return render_template('index.html')

@app.route('/get_data')
def get_data():
    """Parses the airodump CSV and returns the top 5 strongest signals."""
    if not os.path.exists(CSV_FILE):
        return jsonify([])

    try:
        station_line_index = None
        # Find the split point in the airodump CSV
        with open(CSV_FILE, 'r') as f:
            for i, line in enumerate(f):
                if "Station MAC" in line:
                    station_line_index = i
                    break

        if station_line_index is None:
            # Case 1: Only APs found
            data_aps = pd.read_csv(CSV_FILE, skipinitialspace=True)
            data_aps.columns = data_aps.columns.str.strip()
            aps_subset = data_aps[['BSSID', 'Power', 'channel', 'ESSID']].copy()
            aps_subset.columns = ['MAC', 'Power', 'Channel', 'Name']
            combined_df = aps_subset
        else:
            # Case 2: Both APs and Stations found
            data_aps = pd.read_csv(CSV_FILE, nrows=station_line_index - 2, skipinitialspace=True)
            data_aps.columns = data_aps.columns.str.strip()
            aps_subset = data_aps[['BSSID', 'Power', 'channel', 'ESSID']].copy()
            aps_subset.columns = ['MAC', 'Power', 'Channel', 'Name']

            data_stations = pd.read_csv(CSV_FILE, skiprows=station_line_index, skipinitialspace=True)
            data_stations.columns = data_stations.columns.str.strip()
            sta_subset = data_stations[['Station MAC', 'Power', 'Probed ESSIDs']].copy()
            sta_subset.columns = ['MAC', 'Power', 'Name']
            sta_subset['Channel'] = "N/A"
            combined_df = pd.concat([aps_subset, sta_subset], ignore_index=True)

        # Clean Power column and sort
        combined_df['Power'] = pd.to_numeric(combined_df['Power'].astype(str).str.strip(), errors='coerce')
        # -1 is airodump's code for "no signal data," so we filter it out
        topFive = combined_df[(combined_df['Power'] < 0) & (combined_df['Power'] > -100)]
        topFive = topFive.sort_values(by='Power', ascending=False).head(5)

        return jsonify(topFive.to_dict(orient='records'))

    except Exception as e:
        print(f"Error reading CSV: {e}")
        return jsonify([])

@app.route('/start_target/<channel>/<bssid>')
def start_target(channel, bssid):
    """Kills general scan and starts a targeted capture."""
    subprocess.run('sudo rm -f target_capture*', shell=True)

    try:
        subprocess.run(['sudo', 'killall', 'airodump-ng'], stderr=subprocess.DEVNULL)
        
        # Build command. If channel is N/A (a station), we don't use the -c flag
        cmd = ['sudo', 'airodump-ng', '--bssid', str(bssid), '-w', 'target_capture', '--write-interval', '1']
        if channel != "N/A":
            cmd.extend(['-c', str(channel)])
        
        cmd.append(INTERFACE)
        
        subprocess.Popen(cmd)
        return jsonify({"status": "success", "message": f"Targeting {bssid}"})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)