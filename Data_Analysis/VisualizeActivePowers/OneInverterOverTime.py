# Note: I used ChatGPT with my Cal Poly account to generate a lot of the code for this file.
# This code is used to generate a graph for the active power or energy of one inverter over
# some interval of days, where each day is its own line.

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

invNum = 20
monthYear = 'July2025'

df = pd.read_csv(f"Data\ActivePower\{monthYear}\Inverter{invNum}.csv", skipinitialspace=True)
df = df.dropna(axis=1, how="all") # drops extra empty column caused by trailing commas

fig, ax = plt.subplots(figsize=(12, 6))

#for i in range(56, 60, 2): # to see part of month
for i in range(0, df.shape[1], 2): # to see whole month
    timestamps = pd.to_datetime(df.iloc[:, i])
    values = pd.to_numeric(df.iloc[:, i + 1], errors="coerce")

    # Use the actual date only for the label
    day_label = timestamps.iloc[0].strftime("%Y-%m-%d")

    # Put every timestamp on the same fake date
    time_of_day = timestamps.apply(
        lambda t: t.replace(year=2000, month=1, day=1)
    )

    ax.plot(time_of_day, values, label=day_label)

ax.set_xlabel("Time of Day")
ax.set_ylabel(f"Active Power (kW)")
ax.set_title(f"Inverter {invNum} by Day")

ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))

plt.xticks(rotation=45)
ax.grid(True)

# For 30 days, put legend outside the plot
ax.legend(title="Day", bbox_to_anchor=(1.02, 1), loc="upper left")

plt.tight_layout()
plt.show()