# given a file of average power data over one month for every inverter, this code finds the steepest downward
# slope and the associated times for each inverter

import pandas as pd
import numpy as np

monthYear = 'July2025'
outputFile = f'Data_Analysis\MathingIt\Slopes\{monthYear}Slopes.csv'
filepath = f"Data_Analysis\ActivePowerAverages\\FaultyDataDaysRemoved\\{monthYear}APAvgs.csv"
df = pd.read_csv(filepath)

# looking at the data, the sunset drops seem to start around 16:30, which is at index 150 (of 227)
# 14:00 is around the middle of the flat peak, and is at index 120

# get steepest downward slope and associated times for given inverter (using 5 data points)
def getSlopeAndTimesForInverter(inv, df):
    steepestSlope = 0
    steepestTimes = []
    for i in range(5, 220): # for most months, range was (5, 220). for November, use (5, 216)
        times = list(range(i - 5, i))
        aps = df[f'Active Power Inverter {inv} (kW)'][i - 5:i].to_list()

        # dataframe for this line
        df_line = pd.DataFrame({'Time Stamp': times, 'Active Power': aps})

        # get slope of line
        m, c = np.polyfit(df_line['Time Stamp'], df_line['Active Power'], 1)

        if m < steepestSlope:
            steepestSlope = m
            steepestTimes = times[0]

        print('dfsajfkljklj')
        print(m)
        print(times[0])
        print('steepesttimes:', steepestTimes)
    return [steepestSlope, steepestTimes]

getSlopeAndTimesForInverter(63, df)

def generateCSV(name, df):
    # loop through all inverters to find slope and time
    inverters = []
    slopes = []
    times = []
    for i in range(1, 76):
        res = getSlopeAndTimesForInverter(i, df)
        inverters.append(f'Inverter {i}')
        slopes.append(res[0])
        times.append(res[1])

    data = {
        'Inverter': inverters,
        'Slope': slopes,
        'Time': times
    }
    df_new = pd.DataFrame(data)

    # create csv file
    df_new.to_csv(name, index=False)

#generateCSV(outputFile, df)