# given a file of average power data over one month for every inverter along with the time that each sunset
# drop starts, find a quadratic of best fit for the sunset decline

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

monthYear = 'December2025'
output_file = f'Data_Analysis\MathingIt\Concavities\{monthYear}Concavity.csv'
filepath_slopes = f'Data_Analysis\MathingIt\Slopes\{monthYear}Slopes.csv'
filepath_data = f"Data_Analysis\ActivePowerAverages\\FaultyDataDaysRemoved\\{monthYear}APAvgs.csv"

df_slopes = pd.read_csv(filepath_slopes)
df_data = pd.read_csv(filepath_data)

# get each inverter and its corresponding start and end data points to generate the quadratic of best fit
def getCurveStartAndEndForEachInverter(df_slopes, df_data):
    curve_endpoints = {}

    # loop through each inverter
    for i, r in df_slopes.iterrows():
        # get inverter's curve's start time
        name = r['Inverter']
        start = r['Time']
        end = 0

        # get inverter's curve's end time (first 0.0 after start time)
        invAP = df_data[f'Active Power {name} (kW)']
        for i in range(start + 1, len(invAP)):
            if invAP[i] == 0:
                end = i
                break

        curve_endpoints[name] = [start, end]
    
    return curve_endpoints

# get dataframe and coefficients for line of best fit for given inverter
def getCoefficients(inv, df_slopes, df_data, showGraph=False):
    curves = getCurveStartAndEndForEachInverter(df_slopes, df_data)
    start = curves[f'Inverter {inv}'][0]
    end = curves[f'Inverter {inv}'][1]

    # get data for one inverter to generate curve
    data = {
        'times': list(range(start, end + 1)),
        'aps': df_data[f'Active Power Inverter {inv} (kW)'][start:end + 1].to_list()
    }
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

# make csv storing each inverter and its quadratic line of best fit's second derivative
def generateCSV(name, df_slopes, df_data):
    # loop through all inverters to find second derivative
    inverters = []
    second_d = []
    for i in range(1, 76):
        res = getCoefficients(i, df_slopes, df_data)
        inverters.append(f'Inverter {i}')
        second_d.append(res[0] * 2)

    data = {
        'Inverter': inverters,
        'D2': second_d
    }
    df_new = pd.DataFrame(data)

    # create csv file
    df_new.to_csv(name, index=False)

generateCSV(output_file, df_slopes, df_data)