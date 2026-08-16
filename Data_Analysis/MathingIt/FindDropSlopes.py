'''This code finds the steepest downward slope and the associated times for each inverter on given days.'''

import pandas as pd
import numpy as np


# get steepest downward slope and associated times for given inverter on given day from given sunset time
# this is caluclated data points 5 time intervals apart, and the associated time is the middle time
def getSlopeAndTimesForInverter(df, day, sunsetTime):
    steepestSlope = 0
    steepestTimes = []

    # loop through each column to find desired day (alternates between time and power data)
    for i, (col_name, col_data) in enumerate(df.items()):

        # desired day found
        if "Time Stamp" in col_name and col_data[0].split()[0] == day:

            # loop through each time in that day to find steepest slope and its time, only starting around sunset
            aroundSunsetReached = False
            for k in range(5, len(col_data) - 1):
                if col_data[k].split()[1] == sunsetTime:
                    aroundSunsetReached = True
                if not aroundSunsetReached:
                    continue

                power_data = df.iloc[:, i + 1][k - 5:k].to_list()
                times = list(range(k - 5, k))

                # dataframe for this line
                df_line = pd.DataFrame({'Time Stamp': times, 'Active Power': power_data})
        
                # get slope of line
                m, c = np.polyfit(df_line['Time Stamp'], df_line['Active Power'], 1)

                if m < steepestSlope:
                    steepestSlope = m
                    steepestTimes = col_data[times[2]].split()[1]

    return [round(steepestSlope, 2), steepestTimes]

# make csv storing each inverter and its steepest downward slope and corresponding time
def generateCSV(monthYear, sunsetTime):
    # structure to hold data: one inverter column and two columns per day - slope and time
    data = {'Inverter': []}
    days = [] # to keep track of the days that exist

    # make space for slope and time columns for each day for which data exists
    df_power = pd.read_csv(f'Data\\ActivePower\\{monthYear}\\Inverter1.csv')
    for i, (col_name, col_data) in enumerate(df_power.items()):
        if "Time Stamp" in col_name: # in a time column
            day = col_data[0].split()[0]
            days.append(day)
            data[f'{day} Slope'] = []
            data[f'{day} Time'] = []

    # loop through each inverter
    print('calculating slopes')
    for i in range(1, 76):
        print(f'inverter {i}')
        data['Inverter'].append(f'Inverter {i}')
        df = pd.read_csv(f'Data\\ActivePower\\{monthYear}\\Inverter{i}.csv')

        # loop through each day
        for day in days:
            res = getSlopeAndTimesForInverter(df, day, sunsetTime)
            data[f'{day} Slope'].append(res[0])
            data[f'{day} Time'].append(res[1])
        
    # create csv file
    df_new = pd.DataFrame(data)
    df_new.to_csv(f'Data_Analysis\MathingIt\\Slopes\\{monthYear}.csv', index=False)
