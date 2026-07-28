import pandas as pd
from CalcEnergy import getEnergy

monthYear = 'July2025'
days = ['2025-07-01', '2025-07-04',
        '2025-07-10', '2025-07-11', 
        '2025-07-18', '2025-07-19', 
        '2025-07-29', '2025-07-30']
times = ['16:45:00']
output_file = f'Data_Analysis\\EnergyComparisons\\{monthYear}SunsetEnergies.csv'

df = pd.DataFrame()

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

makeInvCol(df)
for day in days:
    makeEnergies(df, monthYear, day, times[0])

df.to_csv(output_file, index=False)