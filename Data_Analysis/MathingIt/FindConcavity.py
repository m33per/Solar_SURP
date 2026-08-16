# this code finds a quadratic of best fit for the sunset decline for each inverter on given days

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from pathlib import Path

monthYear = 'September2025'

output_file = f'Data_Analysis\MathingIt\Concavities\{monthYear}.csv'
filepath_slopes = f'Data_Analysis\MathingIt\Slopes\{monthYear}.csv'
activePowerFolder = f'Data\\ActivePower\\{monthYear}\\'

df_slopes = pd.read_csv(filepath_slopes)

# get dataframe and coefficients for line of best fit for given inverter
def getCoefficients(df_data, day, startTime, showGraph=False):
    activePowers = []
    endTimeIndex = 0
    startTimeIndex = 0

    # get end time for curve, which is first time after start time that active power is < 5
    for i, (col_name, col_data) in enumerate(df_data.items()):
        # desired day found
        if "Time Stamp" in col_name and col_data[0].split()[0] == day:
            startTimePassed = False
            for k in range(len(col_data) - 1):
                if col_data[k].split()[1] == startTime:
                    startTimeIndex = k
                    startTimePassed = True
                if not startTimePassed:
                    continue

                power_data = df_data.iloc[:, i + 1]
                if power_data[k] < 5:
                    endTime = col_data[k]
                    endTimeIndex = k
                    activePowers = power_data[startTimeIndex:endTimeIndex + 1].to_list()
                    break
            break


    # get data for one inverter to generate curve
    data = {
        'times': list(range(startTimeIndex, endTimeIndex + 1)),
        'aps': activePowers
    }
    coefficients = [0,0,0]
    df_curve = None
    if len(data['times']) != len(data['aps']):
        showGraph = False
    else:
        df_curve = pd.DataFrame(data)
        coefficients = np.polyfit(df_curve['times'], df_curve['aps'], 2)

    if showGraph:
        # code copied and slightly modified from google ai
        # 3. Create a smooth line for the best-fit curve
        # Generate 100 evenly spaced points between your min and max X values
        x_curve = np.linspace(df_curve['times'].min(), df_curve['times'].max(), 100)

        # Use np.poly1d to cleanly evaluate the polynomial at those points
        polynomial = np.poly1d(coefficients)
        y_curve = polynomial(x_curve)

        # 4. Plot the results
        plt.scatter(df_curve['times'], df_curve['aps'], color='blue', label='Data Points')
        plt.plot(x_curve, y_curve, color='red', linewidth=2, label='Quadratic Best Fit')
        plt.xlabel('X Values')
        plt.ylabel('Y Values')
        plt.title('Quadratic Line of Best Fit')
        plt.legend()
        plt.grid(True)
        plt.show()

    return coefficients

#getCoefficients(df_data, '2025-07-01', '18:25:00', True)

# make csv storing each inverter and its quadratic line of best fit's second derivative
def generateCSV(monthYear):
    # one column for inverters, one column per day for second derivative
    data = {'Inverter': []}
    days = [] # to keep track of the days that exist

    df_st = pd.read_csv(f'Data_Analysis\\MathingIt\\Slopes\\{monthYear}.csv')
    
    # make space for slope and time columns for each day for which data exists
    df_power = pd.read_csv(f'Data\\ActivePower\\{monthYear}\\Inverter1.csv')
    for i, (col_name, col_data) in enumerate(df_power.items()):
        if "Time Stamp" in col_name: # in a time column
            day = col_data[0].split()[0]
            days.append(day)
            data[f'{day} D2'] = []

    # loop through each inverter
    print('\ncalculating concavities')
    for i in range(1, 76):
        print(f'inverter {i}')
        data['Inverter'].append(f'Inverter {i}')
        df = pd.read_csv(f'Data\\ActivePower\\{monthYear}\\Inverter{i}.csv')

        # find index for this inverter in slopes and times csv file
        index = None
        for k in range(len(df_st['Inverter'])):
            if df_st['Inverter'][k] == f'Inverter {i}':
                index = k
                break

        # loop through each day
        for day in days:
            startTime = df_st[f'{day} Time'][index]
            res = getCoefficients(df, day, startTime)
            data[f'{day} D2'].append(res[0] * 2)
        
    # create csv file
    df_new = pd.DataFrame(data)
    df_new.to_csv(f'Data_Analysis\MathingIt\Concavities\{monthYear}.csv', index=False)

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

mY = 'March2025'
#generateCSV(mY)

'''config_path = Path("config.json")
with open(config_path, "r") as file:
    config = json.load(file)
generateCSV(output_file, activePowerFolder, df_slopes, config["days"][monthYear])'''