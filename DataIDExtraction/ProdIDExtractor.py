import csv

def getIDsByName(name):
    ids = {}

    # open file
    with open('DataIDExtraction\GPM_API_Info_(Inverter_Specific).csv', mode='r', encoding='utf-8', errors='ignore') as file:
        reader = csv.reader(file)
        
        # get header
        header = next(reader) 
        print(f"Headers: {header}\n")
        
        # loop through each row
        for row in reader:
            if row[2] == name:
                ids[row[1]] = f"{row[2]} {row[5]} ({row[4]})"
        
        return ids

ids = getIDsByName('Active Energy')
for k, v in ids.items():
    print(f"'{k}': '{v}',")