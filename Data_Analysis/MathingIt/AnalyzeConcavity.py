import pandas as pd
import json
from pathlib import Path

monthYear = 'July2025'

# get list of strings of inverters outside ranges
def getResults(monthYear, day):
    config_path = Path("config.json")
    with open(config_path, "r") as file:
        config = json.load(file)

    df = pd.read_csv(f'Data_Analysis\MathingIt\Concavities\{monthYear}.csv')

    # calculate numbers to use as boundaries for notable data
    summary = df[f'{day} D2'].describe()
    notableRange = summary['75%'] + (0 * (summary['75%'] - summary['25%']))
    outlierRange = summary['75%'] + (1.5 * (summary['75%'] - summary['25%']))

    results = []

    # loop through each inverter and its second derivative
    for i, r in df.iterrows():
        note = ''
        if r[f'{day} D2'] > config["d2CutOffs"][monthYear]:#notableRange:
            note = f"{r['Inverter']} {r[f'{day} D2']}"
            if r[f'{day} D2'] > outlierRange:
                note += ' OUTLIER'
        if note != '':
            results.append(note)

    return results

# print results
def printResults(monthYear, day):
    res = getResults(monthYear, day)
    for r in res:
        print(r)

if __name__ == '__main__':
    config_path = Path("config.json")
    with open(config_path, "r") as file:
        config = json.load(file)
    printResults(monthYear, config["days"][monthYear][1])