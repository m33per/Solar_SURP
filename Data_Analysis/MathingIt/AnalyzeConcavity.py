import pandas as pd

monthYear = 'May2025'

# get list of strings of inverters outside ranges
def getResults(monthYear):
    df = pd.read_csv(f'Data_Analysis\MathingIt\Concavities\{monthYear}Concavity.csv')

    # calculate numbers to use as boundaries for notable data
    summary = df['D2'].describe()
    notableRange = summary['75%'] + (0 * (summary['75%'] - summary['25%']))
    outlierRange = summary['75%'] + (1.5 * (summary['75%'] - summary['25%']))

    results = []

    # loop through each inverter and its second derivative
    for i, r in df.iterrows():
        note = ''
        if r['D2'] > notableRange:
            note = f"{r['Inverter']} {r['D2']}"
            if r['D2'] > outlierRange:
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