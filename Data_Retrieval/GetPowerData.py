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

    start = [1751342400, 1751428800, 1751515200, 1751601600, 1751688000, 1751774400, 1751860800, 1751947200, 1752033600, 1752120000, 1752206400, 1752292800, 1752379200, 1752465600, 1752552000, 1752638400, 1752724800, 1752811200, 1752897600, 1752984000, 1753070400, 1753156800, 1753243200, 1753329600, 1753416000, 1753502400, 1753588800, 1753675200, 1753761600, 1753848000, 1753934400]
    end = [1751410500, 1751496900, 1751583300, 1751669700, 1751756100, 1751842500, 1751928900, 1752015300, 1752101700, 1752188100, 1752274500, 1752360900, 1752447300, 1752533700, 1752620100, 1752706500, 1752792900, 1752879300, 1752965700, 1753052100, 1753138500, 1753224900, 1753311300, 1753397700, 1753484100, 1753570500, 1753656900, 1753743300, 1753829700, 1753916100, 1754002500]


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
        