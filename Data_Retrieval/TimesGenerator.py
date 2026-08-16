from datetime import datetime

def getAllTimesInMonth(month, year):
    # get number of days for this month
    if month == '02' and int(year) % 4 == 0:
        numDays = 29
    elif month == '02':
        numDays = 28
    elif month in ['01', '03', '05', '07', '08', '10', '12']:
        numDays = 31
    else:
        numDays = 30
    
    # prep lists to hold times
    starts = [0] * numDays
    ends = [0] * numDays

    # get first start and end times
    t = f"{month}/01/{year} 04:00:00"
    dt = datetime(
        int(t[6:10]),
        int(t[0:2]),
        int(t[3:5]),
        int(t[11:13]),
        int(t[14:16]),
        int(t[17:19])
    )
    starts[0] = int(dt.timestamp()) - 25200

    t = f"{month}/01/{year} 22:55:00"
    dt = datetime(
        int(t[6:10]),
        int(t[0:2]),
        int(t[3:5]),
        int(t[11:13]),
        int(t[14:16]),
        int(t[17:19])
    )
    ends[0] = int(dt.timestamp()) - 25200

    # get remaining times
    for i in range(1, numDays):
        starts[i] = starts[0] + (86400 * i)
        ends[i] = ends[0] + (86400 * i)

    return [starts, ends]

'''res = getAllTimesInMonth('02', '2024')
print(len(res[0]))
print("============== START TIMES ==============")
print(res[0])

print("\n============== END TIMES ==============")
print(res[1])'''