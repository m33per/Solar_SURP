import pandas as pd
import matplotlib.pyplot as plt

# show graph of given inverters' energy production for given day from given sunset time
def makeGraph(monthYear, day, time, invNums=[]):
    # read data for month
    df_data = pd.read_csv(f'Data_Analysis\\EnergyComparisons\\SunsetEnergies\\{monthYear}.csv')

    if invNums == []: # show all inverters if none given
        for i in range(1, 76):
            invNums.append(i)
    else:
        invNums.sort()
        for i in range(len(invNums)):
            invNums[i] = int(invNums[i])

    # get energy for each inverter
    energies = []
    for inv in invNums:
        energies.append(df_data[f'{day}'][inv - 1])

    data_to_plot = {'Inverter' : invNums,
                    'Energy (kWh)': energies}
    df = pd.DataFrame(data_to_plot)
    df.plot(kind='bar', x='Inverter', y='Energy (kWh)', legend=False) #color=colors[firstInv:lastInv], legend=False)
    plt.title(f'Energy Comparisons for {day} from {time}')
    plt.show()

