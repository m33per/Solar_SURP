# Note: I used ChatGPT with my Cal Poly account to generate a lot of the code for this file.
# This code is used to generate a graph for the active power or energy of one inverter over
# some interval of days, where each day is its own line.

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# display graph including given converters
def showAvgs(first, last):
    df = pd.read_csv(f"Data_Analysis\July25APAvgs.csv", skipinitialspace=True)
    df = df.dropna(axis=1, how="all") # drops extra empty column caused by trailing commas

    timestamps = pd.to_datetime(df.iloc[:, 0])

    # Put all timestamps on a fake common date
    time_of_day = timestamps.apply(
        lambda t: t.replace(year=2000, month=1, day=1)
    )

    fig, ax = plt.subplots(figsize=(12, 6))

    for i in range(first, last + 1):
        values = pd.to_numeric(df.iloc[:, i], errors="coerce")
        label = df.columns[i]

        ax.plot(time_of_day, values, label=label)

    ax.set_xlabel("Time of Day")
    ax.set_ylabel("Active Power")
    ax.set_title("Inverter Active Power by Time of Day")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))

    plt.xticks(rotation=45)
    ax.grid(True)

    ax.legend(title="Inverter", bbox_to_anchor=(1.02, 1), loc="upper left")

    plt.tight_layout()
    plt.show()

showAvgs(1, 75)