import pandas as pd
from CalcEnergy import getEnergy
import json
from pathlib import Path

config_path = Path("config.json")
with open(config_path, "r") as file:
    config = json.load(file)

monthYear = 'July2025'

# make inverter column
def makeInvCol(df):
    invs = []
    for i in range(1, 76):
        invs.append(i)
    df['Inverter'] = invs

# make energies column
def makeEnergies(df, monthYear, day, time):
    energies = []
    for i in range(1, 76):
        energies.append(round(getEnergy(monthYear, i, day, time), 2))
    df[f'{day} {time}'] = energies

'''output_file = f'Data_Analysis\\EnergyComparisons\\{monthYear}SunsetEnergies.csv'
df = pd.DataFrame()

makeInvCol(df)
for day in config["days"][monthYear]:
    makeEnergies(df, monthYear, day, config["sunsetTimes"][monthYear])

df.to_csv(output_file, index=False)'''