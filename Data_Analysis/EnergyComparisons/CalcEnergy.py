# given a file of inverter data for one month, calculate the amount of energy produced in the given
# time frame for the given day

import pandas as pd

monthYear = 'July2025'
inv = 1

# calculate energy produced for given day from given start time for given inverter
def getEnergy(monthYear, inv, day, startTime):
    filepath = f"Data\ActivePower\{monthYear}\Inverter{inv}.csv"
    df = pd.read_csv(filepath)
    energy = 0

    # loop through each column to find desired day (alternates between time and power data)
    for i, (col_name, col_data) in enumerate(df.items()):

        # desired day found
        if "Time Stamp" in col_name and col_data[0].split()[0] == day:

            # loop through each row to find desired time
            for k in range(len(col_data)):

                # desired time found
                if col_data[k].split()[1] == startTime:

                    power_data = df.iloc[:, i + 1]

                    # loop through power data starting from start time and calculate total energy
                    for j in range(k, len(power_data)):
                        energy += power_data[j] / 12

                    break # exit loop to find desired time

            break # exit loop to find desired day

    return energy

#print(getEnergy(monthYear, inv, '2025-07-32', '17:00:00'))