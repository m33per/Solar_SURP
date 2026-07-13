# Note: I used ChatGPT with my Cal Poly account to generate some code for this file.
# This code is used to create a csv file of the average active power of each inverter
# within a time interval.

import pandas as pd

# time interval to work with
monthYear = 'December2025'

# file to contain avgs
avg_csv = pd.read_csv(f'Data_Analysis\\ActivePowerAverages\\FaultyDataDaysRemoved\{monthYear}APAvgs.csv', index_col=1)

# print times to paste into csv file
def printTimes():
    df = pd.read_csv(f"Data\ActivePower\{monthYear}\Inverter1.csv", skipinitialspace=True)
    for i in df['Time Stamp']:
        print(f"{i.split()[1]},")
#printTimes()

# get a list of columns where data is likely faulty (mostly zeros)
def findColumnsToIgnore(df):
    colsToIgnore = []
    
    # loop through each day in inverter's month data
    for col in df:
        # count number of data points that aren't zero
        nonzeros = 0
        for ap in df[col]:
            if ap != 0:
                nonzeros += 1
        
        # ignore day if too much data is zeros
        # note: I originally had this value set to 120, but 
        if nonzeros < 105:
            colsToIgnore.append(col)

    return colsToIgnore

# get list of avgs in file for one inverter
def getAvgsInFile(invNum, mmYY):
    df = pd.read_csv(f"Data\ActivePower\{mmYY}\Inverter{invNum}.csv", skipinitialspace=True)
    df = df.dropna(axis=1, how="all") # drops extra empty column caused by trailing commas
    avgs = []

    colsToIgnore = findColumnsToIgnore(df)

    # loop through each row, which is a time of day
    for i, r in df.iterrows():
        colName = f'Active Power Inverter {invNum} (kW)'
        sum = 0
        x = 0
        # loop through each value in row, which is the value at that time of day for that day
        if colName not in colsToIgnore:
            sum += r[colName]
            x += 1
        for k in range(1, int(df.shape[1] / 2)):
            colName = f'Active Power Inverter {invNum} (kW).{k}'
            if colName not in colsToIgnore:
                sum += r[colName]
                x += 1
        avg = sum / x
        avgs.append(avg)

    return avgs

numRows = avg_csv.shape[0]
# loop through every inverter
for i in range(1, 76):
    avg_csv[f'Active Power Inverter {i} (kW)'] = getAvgsInFile(i, monthYear)[0:numRows]

# write data to file to contain avgs
avg_csv.to_csv(f'Data_Analysis\\ActivePowerAverages\\FaultyDataDaysRemoved\{monthYear}APAvgs.csv', index=False)