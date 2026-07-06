import subprocess
import DataRequest.ProdIds as ProdIds

start = [1751342400, 1751428800, 1751515200, 1751601600, 1751688000, 1751774400, 1751860800, 1751947200, 1752033600, 1752120000, 1752206400, 1752292800, 1752379200, 1752465600, 1752552000, 1752638400, 1752724800, 1752811200, 1752897600, 1752984000, 1753070400, 1753156800, 1753243200, 1753329600, 1753416000, 1753502400, 1753588800, 1753675200, 1753761600, 1753848000]
end = [1751410500, 1751496900, 1751583300, 1751669700, 1751756100, 1751842500, 1751928900, 1752015300, 1752101700, 1752188100, 1752274500, 1752360900, 1752447300, 1752533700, 1752620100, 1752706500, 1752792900, 1752879300, 1752965700, 1753052100, 1753138500, 1753224900, 1753311300, 1753397700, 1753484100, 1753570500, 1753656900, 1753743300, 1753829700, 1753916100]


for k, v in ProdIds.inverter_active_energies_partial.items():
    # start script to request data
    process = subprocess.Popen(
        ['python', 'Data_Retrieval\GetPowerData.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # get prompt that asks for ID
    promptID = ''
    while 'Enter numerical ID: ' not in promptID:
        char = process.stdout.read(1)
        promptID += char
    print(promptID, end="") # print the prompt

    # provide id
    print(k) # not necessary, but nice to see
    process.stdin.write(f"{k}\n")
    process.stdin.flush()

    # get prompt that asks for value
    promptVal = ''
    while 'Enter the name you would like to use: ' not in promptVal:
        char = process.stdout.read(1)
        promptVal += char
    print(promptVal, end="") # print the prompt

    # provide value
    print(v) # not necessary, but nice to see
    process.stdin.write(f"{v}\n")
    process.stdin.flush()

    # get prompt that asks if user would like to add more ids
    promptUseID = ""
    while "Would you like to add more ids? " not in promptUseID:
        char = process.stdout.read(1)
        promptUseID += char
    print(promptUseID, end="")

    # respond
    print("n")
    process.stdin.write("n\n")
    process.stdin.flush()

    # get prompt that asks for output file name
    promptID = ''
    while 'What should the output file name be? ' not in promptID:
        char = process.stdout.read(1)
        promptID += char
    print(promptID, end="") # print the prompt

    # provide filename
    name = v.split()
    filename = f"Data\July2025ActiveEnergies\{name[2] + name[3]}.csv"
    print(filename) # not necessary, but nice to see
    process.stdin.write(f"{filename}\n")
    process.stdin.flush()
    
    # get confirmation that data was fetched
    doneConf = ""
    while "Done fetching data" not in doneConf:
        char = process.stdout.read(1)
        doneConf += char
    print(doneConf, end="")