# this code finds the steepest downward slope and the associated times for each inverter on given days

import pandas as pd
import numpy as np
import json
from pathlib import Path

'''config_path = Path("config.json")
with open(config_path, "r") as file:
    config = json.load(file)'''

monthYear = 'September2025'
outputFile = f'Data_Analysis\MathingIt\\Slopes\\{monthYear}.csv'
inputFileFolder = f'Data\\ActivePower\\{monthYear}\\'

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

'''df = pd.read_csv('Data\\ActivePower\\July2025\\Inverter75.csv')
res = getSlopeAndTimesForInverter(df, config["days"]['July2025'][0], config["sunsetTimes"]['July2025'])
print(res)'''

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

times = {"January2025": "13:50:00",
"February2025": "14:00:00",
"March2025": "14:20:00",
"April2025": "15:45:00",
"May2025": "16:00:00",
"June2025": "16:20:00",
"July2025": "16:30:00",
"August2025": "16:10:00",
"September2025": "15:40:00",
"October2025": "15:10:00",
"November2025": "13:50:00",
"December2025": "13:50:00"}

mY = 'February2025'
#generateCSV(mY, times[mY])
#generateCSV(outputFile, inputFileFolder, config["days"][monthYear], config["sunsetTimes"][monthYear])