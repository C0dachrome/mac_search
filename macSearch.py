import pandas as pd 

running = True
csv_file = 'text-01.csv'
pd.options.display.max_rows = 9999

# Framing the program
print("Script to continuously check a CSV file dumped by airodump-ng and"
    "print the highest power MAC addresses.", "\n")


with open(csv_file, 'r') as f:
    for i, line in enumerate(f):
        if "Station MAC" in line:
            station_line_index = i
            break

while(running):
    data_aps = pd.read_csv(csv_file, nrows=station_line_index - 2)
    data_stations = pd.read_csv(csv_file, skiprows=station_line_index)
    print(data_aps.to_string())
    for i in range(10):
        print("\n")
    print(data_stations.to_string())
    running = False