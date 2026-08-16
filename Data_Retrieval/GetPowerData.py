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

#----------------------------------------------------------------------------------
# Multiple Time Intervals

def multTimeInts(outputFileName, start, end, prod_id, justOneInt=False):
    gt = goldtree.RequestManager(prod_id)      #Get auth key from API
    gt.authentication_status

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

    start = [1748750400, 1748836800, 1748923200, 1749009600, 1749096000, 1749182400, 1749268800, 1749355200, 1749441600, 1749528000, 1749614400, 1749700800, 1749787200, 1749873600, 1749960000, 1750046400, 1750132800, 1750219200, 1750305600, 1750392000, 1750478400, 1750564800, 1750737600, 1750824000, 1750910400, 1750996800, 1751083200, 1751169600, 1751256000]
    end = [1748818500, 1748904900, 1748991300, 1749077700, 1749164100, 1749250500, 1749336900, 1749423300, 1749509700, 1749596100, 1749682500, 1749768900, 1749855300, 1749941700, 1750028100, 1750114500, 1750200900, 1750287300, 1750373700, 1750460100, 1750546500, 1750632900, 1750805700, 1750892100, 1750978500, 1751064900, 1751151300, 1751237700, 1751324100]


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
        