import subprocess
import ProdIds as ProdIds

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

# start script that requests input to collect data
process = subprocess.Popen(
    ['python', 'Data_Retrieval\GetPowerData.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# give input
provideIDs(process, ProdIds.inverter_custom_active_powers) # change second parameter to change product ids you are requesting
provideTimes(process, "07/06/2025 00:00:00", "07/06/2025 23:00:00") # change times to change interval you are requesting

# get confirmation that data was fetched
doneConf = ""
while "Done fetching data" not in doneConf:
    char = process.stdout.read(1)
    doneConf += char
print(doneConf, end="")