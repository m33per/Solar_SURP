# DST was on November 2, meaning power started collecting 1 hour earlier from Nov 2 and on
# So, shifting up the data for November 1 by 1 hour will make the power collecting hours line
# up with the rest of the days of November.

import pandas as pd

# make a new file for one inverter in March
def makeNewMarchInverterFile(inv):
    outputFile = f'Data\ActivePower\\November2025\Inverter{inv}.csv'
    filepath = f"Data\ActivePower\\November2025\BeforeModifyingForDST\Inverter{inv}.csv"
    df = pd.read_csv(filepath)

    # shift the data up by 1 hour for November 1
    df[f' Active Power Inverter {inv} (kW)'] = df[f' Active Power Inverter {inv} (kW)'].shift(-12)

    # remove last rows that were affected by the shift
    for i in range(216, 228):
        df.drop(i, inplace=True)

    df.to_csv(outputFile, index=False)

# make new files for every inverter in March
for i in range(1, 76):
    makeNewMarchInverterFile(i)