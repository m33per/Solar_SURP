from datetime import datetime

numDays = 30

starts = [0] * numDays
ends = [0] * numDays

t = "07/01/2025 04:00:00"
dt = datetime(
    int(t[6:10]),
    int(t[0:2]),
    int(t[3:5]),
    int(t[11:13]),
    int(t[14:16]),
    int(t[17:19])
)
starts[0] = int(dt.timestamp()) - 25200

t = "07/01/2025 22:55:00"
dt = datetime(
    int(t[6:10]),
    int(t[0:2]),
    int(t[3:5]),
    int(t[11:13]),
    int(t[14:16]),
    int(t[17:19])
)
ends[0] = int(dt.timestamp()) - 25200

for i in range(1, numDays):
    starts[i] = starts[0] + (86400 * i)
    ends[i] = ends[0] + (86400 * i)

print("============== START TIMES ==============")
print(starts)

print("\n============== END TIMES ==============")
print(ends)