# Get start and end times from user in a more human-friendly format to pass into the GetPowerData script

from datetime import datetime
from zoneinfo import ZoneInfo

# get a time from user and return its unix timestamp
def get_time():
    t = input("Enter a time in the following format: MM/DD/YYYY HH:MM:SS\n").strip()
    try:
        dt = datetime(
            int(t[6:10]),
            int(t[0:2]),
            int(t[3:5]),
            int(t[11:13]),
            int(t[14:16]),
            int(t[17:19])
        )
        return int(dt.timestamp()) - 25200
        # POTENTIAL FUTURE PROBLEM: as far as I can tell, 7 hours are added to the desired time,
        # so I fixed this by subtracting 7 hours from the given time
    except:
        return -1

# loop to keep requesting a time from user until their input is valid
def request_time():
    t = get_time()
    while t == -1:
        print("Invalid input.\n")
        t = get_time()
    return t

# gets start and end times from user
def get_times():
    starts =[]
    ends = []

    print("\nGive a start time")
    starts.append(request_time())

    print("\nGive an end time")
    ends.append(request_time())

    return [starts, ends]
