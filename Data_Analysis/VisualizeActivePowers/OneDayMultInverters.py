import pandas as pd
import matplotlib.pyplot as plt
import json
from pathlib import Path
import matplotlib.dates as mdates

monthYear = 'July2025'
dayNum = 0


def makeGraph(monthYear, day, invNums=[]):
    fig, ax = plt.subplots(figsize=(12, 6))

    # get x axis (time)
    df_data = pd.read_csv(f'Data\\ActivePower\\{monthYear}\\Inverter1.csv')
    times = []
    for time in df_data.iloc[:, 0]:
        times.append(time.split()[1])
    del times[-1]

    # if no inverters listed, do all    
    if invNums == []:
        for i in range(1, 76):
            invNums.append(i)
    else:
        # make sure each inverter is an integer
        invNums.sort()
        for i in range(len(invNums)):
            invNums[i] = int(invNums[i])

    # loop through each inverter to plot its power data
    for inv in invNums:
        df_data = pd.read_csv(f'Data\\ActivePower\\{monthYear}\\Inverter{inv}.csv')

        # find correct day for inverter
        for i, (col_name, col_data) in enumerate(df_data.items()):
            if 'Time Stamp' in col_name:
                if col_data[0].split()[0] == day: # found data for this inverter for this day

                    timestamps = pd.to_datetime(df_data.iloc[:, i])
                    values = pd.to_numeric(df_data.iloc[:, i + 1], errors="coerce")
                
                    inv_label = f'Inverter {inv}'
                
                    # Put every timestamp on the same fake date
                    time_of_day = timestamps.apply(
                        lambda t: t.replace(year=2000, month=1, day=1)
                    )
                
                    ax.plot(time_of_day, values, label=inv_label)
                    break

    ax.set_xlabel('Time of Day')
    ax.set_ylabel('Active Powre')
    ax.set_title(f'Active Power for Inverters on {day}')

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    plt.xticks(rotation=45)
    ax.grid(True)

    ax.legend(title="Inverter", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    plt.show()