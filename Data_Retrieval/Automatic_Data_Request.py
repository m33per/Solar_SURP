import subprocess
import Data_Retrieval.ProdIds as ProdIds

# input a single product ID
def provideID(process, id, value):
    # get prompt that asks for ID
    promptID = ''
    while 'Enter numerical ID: ' not in promptID:
        char = process.stdout.read(1)
        promptID += char
    print(promptID, end="") # print the prompt

    # provide id
    print(id) # not necessary, but nice to see
    process.stdin.write(f"{id}\n")
    process.stdin.flush()

    # get prompt that asks if user would like to use the match found
    promptUseID = ""
    while "Enter the name you would like to use: " not in promptUseID:
        char = process.stdout.read(1)
        promptUseID += char
    print(promptUseID, end="")

    # respond
    print(value)
    process.stdin.write(f"{value}\n")
    process.stdin.flush()

# input the start and end times (for one interval only)
def provideTimes(process, start, end):
    # get prompt that asks for start time
    promptUseID = ""
    while "Give a start time\nEnter a time in the following format: MM/DD/YYYY HH:MM:SS" not in promptUseID:
        char = process.stdout.read(1)
        promptUseID += char
    print(promptUseID, end="")

    # respond
    print(f"\n{start}")
    process.stdin.write(f"{start}\n")
    process.stdin.flush()

    # get prompt that asks for end time
    promptUseID = ""
    while "Give an end time\nEnter a time in the following format: MM/DD/YYYY HH:MM:SS" not in promptUseID:
        char = process.stdout.read(1)
        promptUseID += char
    print(promptUseID, end="")

    # respond
    print(f"\n{end}")
    process.stdin.write(f"{end}\n")
    process.stdin.flush()

def provideTimesUnix(process, start, end):
    # get prompt that asks for start time
    promptUseID = ""
    while "Give a start time (unix) " not in promptUseID:
        char = process.stdout.read(1)
        promptUseID += char
    print(promptUseID, end="")

    # respond
    print(f"\n{start}")
    process.stdin.write(f"{start}\n")
    process.stdin.flush()

    # get prompt that asks for end time
    promptUseID = ""
    while "Give an end time (unix) " not in promptUseID:
        char = process.stdout.read(1)
        promptUseID += char
    print(promptUseID, end="")

    # respond
    print(f"\n{end}")
    process.stdin.write(f"{end}\n")
    process.stdin.flush()

# input product IDs from a list
def provideIDs(process, dictIDs):
    listIDs = list(dictIDs)
    for i in range(len(listIDs)):
        provideID(process, listIDs[i], dictIDs[listIDs[i]])

        # get prompt that asks if user would like to add more ids
        promptUseID = ""
        while "Would you like to add more ids? " not in promptUseID:
            char = process.stdout.read(1)
            promptUseID += char
        print(promptUseID, end="")

        # respond
        ans = "y"
        if i == len(listIDs) - 1:
            ans = "n"
        print(ans)
        process.stdin.write(f"{ans}\n")
        process.stdin.flush()

        i += 1

def provideOutputFile(process, filename):
    # get prompt that asks for output file name
    promptID = ''
    while 'What should the output file name be? ' not in promptID:
        char = process.stdout.read(1)
        promptID += char
    print(promptID, end="") # print the prompt

    # provide filename
    print(filename) # not necessary, but nice to see
    process.stdin.write(f"{filename}\n")
    process.stdin.flush()

# start script that requests input to collect data
process = subprocess.Popen(
    ['python', 'Data_Retrieval\GetPowerData.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

#start_feb2025 = [1738386000, 1738472400, 1738558800, 1738645200, 1738731600, 1738818000, 1738904400, 1738990800, 1739077200, 1739163600, 1739336400, 1739422800, 1739509200, 1739682000, 1739941200, 1740027600, 1740114000, 1740200400, 1740286800, 1740373200, 1740459600, 1740546000, 1740632400, 1740718800]
#end_feb2025 = [1738454100

# give input
provideIDs(process, ProdIds.inverter_custom_active_powers) # change second parameter to change product ids you are requesting
provideOutputFile(process, "DataRequest\\Test.csv")
#provideTimes(process, "02/01/2025 00:00:00", "02/01/2025 23:00:00") # change times to change interval you are requesting
provideTimesUnix(process, 1738386000, 1738454100)

# get confirmation that data was fetched
doneConf = ""
while "Done fetching data" not in doneConf:
    char = process.stdout.read(1)
    doneConf += char
print(doneConf, end="")