# DST was on March 9, meaning power started collecting 1 hour later from March 9 and on
# So, shifting up the data for every day from March 9 and on by 1 hour will make the power
# collecting hours line up with the first days of March.

import pandas as pd

# make a new file for one inverter in March
def makeNewMarchInverterFile(inv):
    #outputFile = f'Data\ActivePower\March2025\Inverter{inv}.csv'
    filepath = f"Data\ActivePower\March2025\Inverter{inv}.csv"
    df = pd.read_csv(filepath)

    # March 9 data is in the column ' Active Power Inverter 1 (kW).5'
    # loop through all days in March from March 9 and up and shift the data up by 1 hour
    for i in range(5, 28):
        df[f' Active Power Inverter {inv} (kW).{i}'] = df[f' Active Power Inverter {inv} (kW).{i}'].shift(-12)


    df.to_csv(filepath, index=False)

# make new files for every inverter in March
def updateMarchForDST():
    for i in range(1, 76):
        makeNewMarchInverterFile(i)

updateMarchForDST()