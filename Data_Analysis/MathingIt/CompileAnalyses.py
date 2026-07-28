import pandas as pd
import numpy as np
import re

import AnalyzeConcavity
import AnalyzeDropSlopes
import AnalyzeDropTimes

months = [
    'January2025',
    'February2025',
    'April2025',
    'May2025',
    'June2025',
    'July2025',
    'August2025',
    'September2025',
    'October2025',
    'November2025',
    'December2025'
]

months = ['July2025']

# dictionaries to store each inverter and the number of months its metric is notably poor
bad_slopes2025 = {}
bad_times2025 = {}
bad_d2s2025 = {}
for i in range(1, 76):
    bad_slopes2025[f'Inverter {i}'] = 0
    bad_times2025[f'Inverter {i}'] = 0
    bad_d2s2025[f'Inverter {i}'] = 0

# loop through each month
for month in months:
    print()
    print('-'*80)
    print(month)
    print('-'*80)
    # get the poorly performing inverters by each metric
    bad_slopes = AnalyzeDropSlopes.getResults(month)
    #bad_times = AnalyzeDropTimes.getResults(month)
    bad_d2s = AnalyzeConcavity.getResults(month)

    # increment the total count for each poorly performing inverter
    for s in bad_slopes:
        temp = s.split()
        inv = f'{temp[0]} {temp[1]}'
        bad_slopes2025[inv] += 1
    '''for t in bad_times:
        temp = t.split()
        inv = f'{temp[0]} {temp[1]}'
        bad_times2025[inv] += 1'''
    for d in bad_d2s:
        temp = d.split()
        inv = f'{temp[0]} {temp[1]}'
        bad_d2s2025[inv] += 1

print('Bad slope total count')
print(bad_slopes2025)
'''print('Bad time total count')
print(bad_times2025)'''
print('Bad concavity total count')
print(bad_d2s2025)

print('-'*80)

# add the counts of all three metrics for each inverter
inverters = []
counts = []
for i in range(1, 76):
    inverters.append(f'{i}')
    counts.append(bad_slopes2025[f'Inverter {i}'] + bad_times2025[f'Inverter {i}'] + bad_d2s2025[f'Inverter {i}'])

print('Badness total count')
print(counts)

# summarize the data of the total counts
df = pd.DataFrame({'Inverter': inverters, 'Count': counts})
summary = df.describe()
print()
print(summary)
print('-'*80)

# find thresholds for determining potentially poorly performing inverters
summary_75 = summary.loc['75%', 'Count']
summary_25 = summary.loc['25%', 'Count']
notableRange = summary_75 + (0 * (summary_75 - summary_25))
outlierRange = summary_75 + (1.5 * (summary_75 - summary_25))

# find the inverters that meet those thresholds
results = []
for i in range(0, 75):
    note = ''
    if counts[i] > notableRange:
        note = f"Inverter {i + 1}: {counts[i]}"
        if counts[i] > outlierRange:
            note += ' OUTLIER'
    if note != '':
        results.append(note)

print(results)
for r in results:
    print(f"{re.split(' |:', r)[1]}, ", end='')
print()