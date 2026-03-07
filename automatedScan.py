import asyncio
import csv
import os
import subprocess
import glob
import time 
import pandas as pd
import io
import datetime

INTERFACE = 'wlan1'

CSV_PREFIX = '/dev/shm/scan'
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
def parse_csv(testing):

    if not testing:
        current_file = get_latest_csv()
        if not current_file or not os.path.exists(current_file):
            return []
    else: 
        current_file = "fake-01.csv"
        
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

    subprocess.run(["sudo", "pkill", "airodump-ng"], stderr=subprocess.DEVNULL)
    subprocess.run(["sudo", "rfkill", "unblock", "wlan"], stderr=subprocess.DEVNULL)
    
    # clean up old scan files
    for f in glob.glob(f"{CSV_PREFIX}*"):
        try: os.remove(f)
        except: pass

    cmd = [
        "sudo", "airodump-ng", INTERFACE,
        "-w", CSV_PREFIX,
        "--output-format", "csv",
        "--write-interval", "1",
        "--background", "1"
    ]
    
    if ch and bssid:
        cmd.extend(["-c", str(ch), "--bssid", bssid])

    # use Popen instead of run to avoid waiting for the process to finish, and redirect all output to DEVNULL to keep the terminal clean
    subprocess.Popen(
        cmd, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL, 
        stdin=subprocess.DEVNULL,
        preexec_fn=os.setpgrp 
    )

#################################################################################
#
# run_scan(mac, ch) - runs a guided scan on the target mac and channel
#
#################################################################################
def run_scan(mac, ch, name, testing):
    measurements = [0,0,0,0,0]


    #gets the datetime as a datetime object, then formats it as a string
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    #replaces spaces with underscores and colons with dashes to make it filename friendly
    current_datetime = current_datetime.replace(" ", "_").replace(":", "-")

    aud_num = input("auditorium number? ")
    
    #in case the file already exists, we append to it instead of creating a new one 
    try:
        file = open(f"measurements_th_{aud_num}.txt", "x")
    except FileExistsError:
        #for some reason, this deletes the file instead of appending to it. Not currently 
        #an issue, but something to remember
        file = open(f"measurements_th_{aud_num}.txt", "w")
        file.write(f"new scan yo\n")
    file.write(f"Starting scan at {current_datetime}\nTheatre {aud_num}")


    #all positions we want to scan at - we will prompt the user to move to each one before taking measurements
    positions = ["top left", "top right", "middle left", "middle center (standing)", "middle center (seated)", "bottom left", "bottom right"]
    
    #iterate through each scan position, prompting the user to move there each time.
    for scan_num in range(7):

        input(f"Targeting {mac}. Move to {positions[scan_num]}, then hit enter...")
        if not testing:
            run_airodump(ch, mac)

        for i in range(5):
            time.sleep(2)
            data = parse_csv(testing)
            
            # Filter list to find the specific target MAC and Name
            target_row = next((item for item in data if item["MAC"].lower() == mac.lower() and item["Name"] == name), None)
            
            if target_row:
                measurements[i] = target_row['Power']
                print(f"Reading {i+1}: {measurements[i]} dBm")
            else:
                print(f"Reading {i+1}: Target not found in this sample")
                measurements[i] = 0

        #determine the number of valid readings (non-zero) and calculate the total 
        total = 0
        valid_readings = 0
        for j in measurements:
            if j != 0:
                total = total + j
                valid_readings += 1

        if valid_readings > 0:
            #calculate the average of the valid readings and print it, also write it to the file
            top_left = total / valid_readings
            print(f"{positions[scan_num]} measurement (Avg of {valid_readings}): {top_left} dBm")
            file.write(f"{positions[scan_num]} Measurement (Avg of {valid_readings}): {top_left} dBm\n")
        else:
            print("Could not get any valid readings for the target.")

    print("Scan complete. Results saved to file.")
    
    if not testing:
        print("killing airodump process...")
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
        if not testing:
            run_airodump()
        else:
            print(testing)
            print("looks like youre on windows - using fake scan file")
            time.sleep(1)

        while True:

            #this uses "cls" if on windows and otherwise uses clear
            os.system('cls' if testing else 'clear')

            all_devices = parse_csv(testing)

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

        print("\nKeyboard Interrupt. Continuing...")

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
                target_name = chosen_target['Name']
                if not target_name:
                    target_name = chosen_target['MAC']
                running = False
            else: 
                print("invalid option, try again")
                running = True
        
        print(f"you chose {target_mac} on channel {target_ch}")

        run_scan(target_mac, target_ch, target_name, testing)