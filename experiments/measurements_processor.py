import sys
import csv
from datetime import datetime, time

measurements_file = sys.argv[1]
with open(measurements_file, newline='') as f:
    results_reader = csv.DictReader(f, delimiter=' ')
    sorted_results = sorted(results_reader, key=lambda row: row['Time'])
    #print(sorted_results)

    for row in sorted_results:
        time_value = row['Time']
        row['Time'] = datetime.strptime(time_value, '%H:%M:%S')

    start = sorted_results[0]['Time']
    for row in sorted_results:
        row['Time'] = (row['Time'] - start).total_seconds()

    print(sorted_results)

scenario_name, extension = measurements_file.split('.')
processed_file = '.'.join([scenario_name + '_processed', extension])
print(processed_file)

with open(processed_file, 'w', newline='') as f:
    fieldnames = ['Time', 'VDUs']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(sorted_results)

