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

    start = [1746072000, 1746158400, 1746244800, 1746331200, 1746417600, 1746504000, 1746590400, 1746676800, 1746763200, 1746849600, 1746936000, 1747022400, 1747108800, 1747281600, 1747886400, 1747972800, 1748059200, 1748145600, 1748232000, 1748318400, 1748404800, 1748491200, 1748577600, 1748664000]
    end = [1746140100, 1746226500, 1746312900, 1746399300, 1746485700, 1746572100, 1746658500, 1746744900, 1746831300, 1746917700, 1747004100, 1747090500, 1747176900, 1747349700, 1747954500, 1748040900, 1748127300, 1748213700, 1748300100, 1748386500, 1748472900, 1748559300, 1748645700, 1748732100]

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
        