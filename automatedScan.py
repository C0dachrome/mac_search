#################################################################################
#
# automatedScan.py
#
#################################################################################
import asyncio
import csv
import os
import subprocess
import glob
import time 
import pandas as pd
import io

INTERFACE = 'wlan1'

CSV_PREFIX = '/device/shm/scan'
# CSV_PREFIX = 'scan' #version to run on windows laptop

TARGET_MAC = None

#################################################################################
#
# get_latest_csv() - returns the most recently created CSV file in the directory
#
#################################################################################
def get_latest_csv():
    files = glob.glob(f"{CSV_PREFIX}-*.csv")
    if not files:
        return None
    return max(files, key=os.path.getmtime)

#################################################################################
#
# parse_csv() - reads the latest CSV file and returns a list of dictionaries
#  with device info
#################################################################################
def parse_csv(fake_scan):

    if not fake_scan:
        current_file = get_latest_csv()
        if not current_file or not os.path.exists(current_file):
            return []
    else: 
        current_file = "scan-01.csv"
        
    try:
        with open(current_file, 'r', newline='', errors='ignore') as f:

            # airodump files have two tables; we only want the first one (APs)
            content = f.read().split('\n\n')[0]
            
        # skipinitialspace=True handles the " Power" vs "Power" issue automatically
        df = pd.read_csv(io.StringIO(content), skiprows=1, skipinitialspace=True)
        
        # Clean any remaining whitespace from column names just in case
        df.columns = df.columns.str.strip()
        
        # Verify 'Power' exists before processing
        if 'Power' not in df.columns:
            return []

        # Convert Power to numeric and filter out -1 (no signal)
        df['Power'] = pd.to_numeric(df['Power'], errors='coerce')
        df = df.dropna(subset=['Power']).query("Power != -1")
        
        # Map to dictionary format
        return df.apply(lambda row: {
            "MAC": str(row['BSSID']).strip(),
            "Power": int(row['Power']),
            "Channel": str(row['channel']).strip(),
            "Name": str(row['ESSID']).strip() if pd.notna(row['ESSID']) else "Unknown"
        }, axis=1).tolist()

    except Exception as e:
        print(f"Exception when parsing csv: {e}")
        return []

#################################################################################
#
# run_airodump(ch, bssid) - runs a scan on the target mac and channel if provided
# otherwise runs a general scan 
#################################################################################
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

#################################################################################
#
# run_scan(mac, ch) - runs a guided scan on the target mac and channel
#
#################################################################################
def run_scan(mac, ch):
    measurements = [0,0,0,0]
    input("move to left corner, when youre there hit enter")
    
    run_airodump(ch, mac)
    time.sleep(2)
    measurements[0] = parse_csv(False)[0]['Power']
    time.sleep(2)
    measurements[1] = parse_csv(False)[0]['Power']
    time.sleep(2)
    measurements[2] = parse_csv(False)[0]['Power']
    time.sleep(2)
    measurements[3]= parse_csv(False)[0]['Power']
    
    total = 0
    for i in measurements:
        total = total + i

    top_left = total / 4

    subprocess.run(["sudo", "pkill", "airodump-ng"])

#################################################################################
#
# main function of the program
#
#################################################################################
if __name__ == '__main__':

    top_5 = []

    testing = os.name == 'nt'

    try:
        #uncomment when running on correct device
        if not testing:
            fake_scan = False
            run_airodump()
        else:
            fake_scan = True
            print("looks like youre on windows - using fake scan file")
            time.sleep(1)

        while True:

            #this uses "cls" if on windows and otherwise uses clear
            os.system('cls' if testing else 'clear')

            all_devices = parse_csv(fake_scan)

            if not all_devices:
                print("scanning")
            else:
                top_5 = sorted(all_devices, key=lambda x: x['Power'], reverse=True)[:5]

                print(f"{'num':<3} | {'MAC':<20} | {'PWR':<5} | {'CH':<3} | {'ESSID'}")
                print("-" * 50)
                
                for i, device in enumerate(top_5, start=1):

                    #this prints the MAC, pwr, etc for each device by iterating using device variable.
                    #also, the formatting here uses < to left align and the number after for column width
                    print(f"{i:<3} | {device['MAC']:<20} | {device['Power']:<5} | {device['Channel']:<3} | {device['Name']}")

            time.sleep(0.5)

    except KeyboardInterrupt:

        print("Keyboard Interrupt. Continuing...")


        #another check to see if youre on windows, if not use sudo pkill to get rid of 
        #old airodump processes
        if not testing:
            subprocess.run(["sudo", "pkill", "airodump-ng"])


        running = True

        while running:
            
            try:
                if top_5:
                    target = int(input(f"Which MAC would you like to target? (1-{len(top_5)}) "))
                else: 
                    raise Exception
            except: 
                target = 0
            
            if target >= 1 and target <= len(top_5):
                chosen_target = top_5[target-1]
                target_mac = chosen_target['MAC']
                target_ch = chosen_target['Channel']
                running = False
            else: 
                print("invalid option, try again")
                running = True
        
        print(f"you chose {target_mac} on channel {target_ch}")

        if not testing:
            print("running guided scan")
            run_scan(target_mac, target_ch)
        
        run_scan(target_mac, target_ch)

