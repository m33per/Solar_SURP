import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path

monthYear = 'July2025'
dayNum = 0

# July2025 info
bad_invs = []#[44, 46, 47, 48, 58, 59, 60, 61, 62, 63, 64, 65, 72, 73]
colors = []
for i in range(75):
    if i in bad_invs:
        colors.append('red')
    else:
        colors.append('skyblue')

def makeGraph(monthYear, day, time, invNums=[]):
    # read data for month
    df_data = pd.read_csv(f'Data_Analysis\\EnergyComparisons\\{monthYear}SunsetEnergies.csv')

    if invNums == []:
        for i in range(1, 76):
            invNums.append(i)
    else:
        invNums.sort()
        for i in range(len(invNums)):
            invNums[i] = int(invNums[i])
    energies = []
    for inv in invNums:
        energies.append(df_data[f'{day}'][inv - 1])

    # select one day
    '''data_to_plot = {'Inverter' : df_data['Inverter'][firstInv-1:lastInv],
                    'Energy (kWh)': df_data[f'{day}'][firstInv-1:lastInv]}'''
    data_to_plot = {'Inverter' : invNums,
                        'Energy (kWh)': energies}
    df = pd.DataFrame(data_to_plot)

    df.plot(kind='bar', x='Inverter', y='Energy (kWh)', legend=False) #color=colors[firstInv:lastInv], legend=False)
    plt.title(f'Energy Comparisons for {day} from {time}')

    plt.show()

'''
config_path = Path("config.json")
with open(config_path, "r") as file:
    config = json.load(file)

for day in config["days"][monthYear]:
    makeGraph(monthYear, day, config["sunsetTimes"][monthYear], 1, 75)
    '''
