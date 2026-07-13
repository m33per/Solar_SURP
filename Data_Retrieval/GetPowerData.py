import goldtree
import GetTimesFromUser
from datetime import datetime

# Production IDs to query from must be set inside of request_manager.py from the goldtree sdk
# This script takes the data pulled by the sdk and formats it into an CSV file for easier analysis

# Data can be grouped in the following ways: 
    # "raw",
    # "quarter",
    # "day",
    # "month",
    # "year",
    # "hour",
    # "halfyear",
    # "tenminute"

gt = goldtree.RequestManager()      #Get auth key from API
gt.authentication_status

#----------------------------------------------------------------------------------
# Multiple Time Intervals

def multTimeInts(outputFileName, start, end, justOneInt=False):
    # just one interval
    if justOneInt:
        #res = GetTimesFromUser.get_times() # request start and end times from user
        res = GetTimesFromUser.get_times_unix()
        start = res[0]
        end = res[1]

    i = 0
    times = []
    values = []
    columns = []
    for s in start:     # Gets data for each time interval and puts it into the appropriate array
        power_df = gt.get_power_production_data(start[i], end[i], "raw")
        times.append(power_df.index)
        values.append(power_df.values)
        columns.append(power_df.columns)
        i += 1
    print("Done fetching data")

    with open(outputFileName, "w") as txt_file:       # Write data to CSV file
        k = 0
        for t in times:     # First row
            txt_file.write("Time Stamp")
            for line in columns[k]:
                txt_file.write("".join(", " + line))    # Production ID labels
            txt_file.write(", ")
            k += 1
        txt_file.write("\n")
        i = 0
        for line in t:
            k = 0
            for t in times:
                j = 0
                txt_file.write("".join(str(t[i])))      # Time stamps
                for x in values[k][i]:
                    txt_file.write("".join(", " + str(values[k][i][j]).strip()))    # Data values 
                    j += 1
                txt_file.write(", ")
                k += 1
            txt_file.write("\n")
            i += 1

if __name__ == '__main__':
    outputFileName = input("What should the output file name be? ")

    start = [1761969600, 1762056000, 1762142400, 1762228800, 1762315200, 1762401600, 1762488000, 1762574400, 1762660800, 1762747200, 1762833600, 1762920000, 1763092800, 1763179200, 1763265600, 1763352000, 1763438400, 1763524800, 1763611200, 1763697600, 1763784000, 1763870400, 1763956800, 1764043200, 1764129600, 1764216000, 1764302400, 1764388800, 1764475200]
    end = [1762037700, 1762124100, 1762210500, 1762296900, 1762383300, 1762469700, 1762556100, 1762642500, 1762728900, 1762815300, 1762901700, 1762988100, 1763160900, 1763247300, 1763333700, 1763420100, 1763506500, 1763592900, 1763679300, 1763765700, 1763852100, 1763938500, 1764024900, 1764111300, 1764197700, 1764284100, 1764370500, 1764456900, 1764543300]

    multTimeInts(outputFileName, start, end)
        
#----------------------------------------------------------------------------------
# Single Time Interval 

# 7/12/2019 16:00-22:00 day 193
# start = 1562947200
# end   = 1562968800
     
# power_df = gt.get_power_production_data(start, end, "raw")    # Get data from API
# print("Done fetching data")
# times = power_df.index
# values = power_df.values


# with open("API_output.csv", "w") as txt_file:     # Write to CSV file
    # txt_file.write("Time Stamp")
    # for line in power_df.columns:     # First row
        # txt_file.write("".join(", " + line))      # Production ID labels
    # txt_file.write("\n")
    # i = 0
    # for line in times:
        # j = 0
        # txt_file.write("".join(str(times[i])))
        # for x in values[i]:
            # txt_file.write("".join(", " + str(values[i][j]).strip()))     # Data values
            # j += 1
        # txt_file.write("".join("\n"))
        # i += 1
        