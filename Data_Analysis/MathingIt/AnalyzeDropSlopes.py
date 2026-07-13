import pandas as pd

monthYear = 'July2025'

# get list of strings of inverters outside ranges
def getResults(monthYear):
    df = pd.read_csv(f'Data_Analysis\MathingIt\Slopes\{monthYear}Slopes.csv')

    # calculate numbers to use as boundaries for notable data
    summary = df['Slope'].describe()
    notableRange = summary['25%'] - (0 * (summary['75%'] - summary['25%']))
    outlierRange = summary['25%'] - (1.5 * (summary['75%'] - summary['25%']))

    results = []

    # loop through each inverter and its slope
    for i, r in df.iterrows():
        note = ''
        if r['Slope'] < notableRange:
            note = f"{r['Inverter']} {r['Slope']}"
            if r['Slope'] < outlierRange:
                note += ' OUTLIER'
        if note != '':
            results.append(note)

    return results

# print results
def printResults(monthYear):
    res = getResults(monthYear)
    for r in res:
        print(r)

printResults(monthYear)