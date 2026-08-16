import pandas as pd
import json
from pathlib import Path

# make energies column
def makeEnergies(monthYear, time):
    # generate top row for csv file (Inverter, Date 1, Date 2,...)
    topRow = ['Inverter']
    filepath = f"Data\ActivePower\{monthYear}\Inverter1.csv"
    df_power = pd.read_csv(filepath)
    for i, (col_name, col_data) in enumerate(df_power.items()):
        if "Time Stamp" in col_name: # in a time column
            topRow.append(col_data[0].split()[0])
    df = pd.DataFrame(columns=topRow)

    # loop through each inverter to generate file row by row
    for k in range(1, 76):
        invRow = [k]
        filepath = f"Data\ActivePower\{monthYear}\Inverter{k}.csv"
        df_power = pd.read_csv(filepath)
        energy = 0

        # loop through each column (day)
        for i, (col_name, col_data) in enumerate(df_power.items()):
            if "Time Stamp" in col_name: # in a time column
                for k in range(len(col_data)): # loop through each row to find desired time

                    # for this day, sunset curve time is reached
                    if col_data[k].split()[1] == time:  
                        power_data = df_power.iloc[:, i + 1]

                        # loop through remaining power data for this day to calculate total energy
                        for j in range(k, len(power_data)):
                            energy += power_data[j] / 12

                        break # exit loop to find sunset time, so we can finish this day

                # add energy data for this day to this inverter's list
                invRow.append(round(energy, 2))
        
        # add this inverter's data for the month to df
        df.loc[len(df)] = invRow

    return df

# make file holding energy data for given days in month
def makeFile(monthYear):
    config_path = Path("config.json")
    with open(config_path, "r") as file:
        config = json.load(file)
        
    output_file = f'Data_Analysis\\EnergyComparisons\\{monthYear}SunsetEnergies.csv'

    df = makeEnergies(monthYear, config["sunsetTimes"][monthYear])
    '''for day in config["days"][monthYear]:
        makeEnergies(df, monthYear, day, config["sunsetTimes"][monthYear])'''

    df.to_csv(output_file, index=False)
