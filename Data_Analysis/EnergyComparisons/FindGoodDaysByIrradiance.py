# script to find days in given month that were likely not cloudy based on irradiance
import pandas as pd

monthYear = 'August2025'

filepath = f"Data\Irradiance\{monthYear}.csv"
df = pd.read_csv(filepath)

# find row index to use for sunset time
def findSunsetTimeIndex(df, sunsetTime):
    times = df['Time Stamp']
    for i in range(0, len(times)):
        if times[i].split()[1] == sunsetTime:
            return i
    return 0

# get list of days that were not cloudy starting at the sunset time
def getGoodDays(df, sunsetTime):
    goodDays = []

    # loop through each column
    for i, (col_name, col_data) in enumerate(df.items()):

        # go through data for one day
        if "Time Stamp" in col_name:
            upness = 0
            numUps = 0 # counter for 'jaggedness' of irradiance

            # loop through each row in corresponding irradiance data column starting at sunsetTime
            irr = df.iloc[:, i + 1]
            for k in range(sunsetTime + 1, len(irr)):
                if irr[k] > irr[k - 1]:
                    upness += irr[k] - irr[k - 1]
                    numUps += 1

            # if no jaggedness, add date to good days list
            if upness < 30:
                goodDays.append(col_data[0].split()[0])

    return goodDays
