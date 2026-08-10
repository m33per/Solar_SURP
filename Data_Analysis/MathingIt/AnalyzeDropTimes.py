import pandas as pd

monthYear = 'November2025'

# get list of strings of inverters outside ranges
def getResults(monthYear):
    df = pd.read_csv(f'Data_Analysis\MathingIt\Slopes\{monthYear}.csv')

    # calculate numbers to use as boundaries for notable data
    summary = df['Time'].describe()
    notableRange = summary['25%'] - (0 * (summary['75%'] - summary['25%']))
    outlierRange = summary['25%'] - (1.5 * (summary['75%'] - summary['25%']))

    results = []

    # loop through each inverter and its drop time
    for i, r in df.iterrows():
        note = ''
        if r['Time'] < notableRange:
            note = f"{r['Inverter']} {r['Time']}"
            if r['Time'] < outlierRange:
                note += ' OUTLIER'
        if note != '':
            results.append(note)

    return results

# print results
def printResults(monthYear):
    res = getResults(monthYear)
    for r in res:
        print(r)

if __name__ == '__main__':
    printResults(monthYear)