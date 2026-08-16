import pandas as pd
import json
from pathlib import Path

# get list of strings of inverters outside ranges
def getResults(monthYear, day):
    config_path = Path("config.json")
    with open(config_path, "r") as file:
        config = json.load(file)

    df = pd.read_csv(f'Data_Analysis\MathingIt\Slopes\{monthYear}.csv')

    # calculate number to use as boundary for outliers
    summary = df[f'{day} Slope'].describe()
    outlierRange = summary['25%'] - (1.5 * (summary['75%'] - summary['25%']))

    results = []

    # loop through each inverter and its slope
    for i, r in df.iterrows():
        note = ''

        # note inverter if value meets configured threshold
        if r[f'{day} Slope'] < config["slopeCutOffs"][monthYear]:#notableRange:
            note = f"{r['Inverter']} {r[f'{day} Slope']}"
            if r[f'{day} Slope'] < outlierRange:
                note += ' OUTLIER'
        if note != '':
            results.append(note)

    return results

# print results
def printResults(monthYear, day):
    res = getResults(monthYear,day)
    for r in res:
        print(r)
