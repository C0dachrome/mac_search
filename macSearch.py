import pandas as pd 

running = True
csv_file = 'text-01.csv'
pd.options.display.max_rows = 9999

# Framing the program
print("Script to continuously check a CSV file dumped by airodump-ng and"
    "print the highest power MAC addresses.", "\n")


#File parsing to locate the station data marker
#Opens the CSV file in read mode and iterates through each line,
#searching for the "Station MAC" string which marks the boundary between
#AP (Access Point) data and Station data. Once found, stores the line index
#in station_line_index and breaks out of the loop for later use in data splitting.

with open(csv_file, 'r') as f:
    for i, line in enumerate(f):
        if "Station MAC" in line:
            station_line_index = i
            break

while(running):

    #aps from top to 2 before the "station MAC" marker
    data_aps = pd.read_csv(csv_file, nrows=station_line_index - 2)

    #remove spaces
    data_aps.columns = data_aps.columns.str.strip()

    #seperate one for stations, start at "station MAC"
    data_stations = pd.read_csv(csv_file, skiprows=station_line_index)

    #remove spaces
    data_stations.columns = data_stations.columns.str.strip()

    #grab the bssid, pwr, and essid columns and put them into a new dataframe
    aps_subset = data_aps[['BSSID', 'Power', 'ESSID']].copy()

    #rename the columns of new dataframe for readability
    aps_subset.columns = ['MAC', 'Power', 'Name']

    #same setup just with the station MACs instead of the AP ones
    sta_subset = data_stations[['Station MAC', 'Power', 'Probed ESSIDs']].copy()
    sta_subset.columns = ['MAC', 'Power', 'Name']

    combined_df = pd.concat([aps_subset, sta_subset], ignore_index=True)


    #strip then convert to numbers
    combined_df['Power'] = pd.to_numeric(combined_df['Power'].astype(str).str.strip(), errors='coerce')
    combined_df['Power'] = pd.to_numeric(combined_df['Power'], errors='coerce')

    #find top 5 by sorting by power then grabbing top 5 values
    topFive = combined_df.sort_values(by='Power', ascending=False).head(5)

    print(topFive.to_string())
    running = False