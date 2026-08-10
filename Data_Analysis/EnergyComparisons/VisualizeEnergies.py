import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path

config_path = Path("config.json")
with open(config_path, "r") as file:
    config = json.load(file)

monthYear = 'July2025'
dayNum = 0

# July2025 info
bad_invs = [44, 46, 47, 48, 58, 59, 60, 61, 62, 63, 64, 65, 72, 73]
colors = []
for i in range(75):
    if i in bad_invs:
        colors.append('red')
    else:
        colors.append('skyblue')

def makeGraph(monthYear, day, time, firstInv, lastInv):
    # read data for month
    df_data = pd.read_csv(f'Data_Analysis\\EnergyComparisons\\{monthYear}SunsetEnergies.csv')

    # select one day
    data_to_plot = {'Inverter' : df_data['Inverter'][firstInv-1:lastInv],
                    'Energy (kWh)': df_data[f'{day} {time}'][firstInv-1:lastInv]}
    df = pd.DataFrame(data_to_plot)

    df.plot(kind='bar', x='Inverter', y='Energy (kWh)', color=colors[firstInv:lastInv], legend=False)
    plt.title(f'Energy Comparisons for {day} from {time}')

    plt.show()

'''for day in config["days"][monthYear]:
    makeGraph(monthYear, day, config["sunsetTimes"][monthYear], 1, 75)
    '''
