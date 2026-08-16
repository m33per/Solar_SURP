import pandas as pd
import ProdIds
from GetPowerData import multTimeInts
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from urllib.error import HTTPError
import TimesGenerator
from pathlib import Path

class DataPull:
    monthNames = ['January',
                  'February',
                  'March',
                  'April',
                  'May',
                  'June',
                  'July',
                  'August',
                  'September',
                  'October',
                  'November',
                  'December']
    month = ''
    year = ''
    startTimes = []
    endTimes = []
    badDays = []
    stopRunning = False

    # create data files and store them in given directory
    def generateFiles(self, isInv, invNums=[]):
        # remove bad days from startTimes and endTimes
        self.badDays.sort()
        for item in reversed(self.badDays):
            del self.startTimes[item - 1]
            del self.endTimes[item - 1]

        # items are either inverters or irradiance ids
        items = {}
        if isInv:
            if invNums == []:
                items = ProdIds.inverter_active_powers
            else:
                for inv in invNums:
                    prod_id = ProdIds.inverter_prod_id_mapping[inv]
                    items[prod_id] = ProdIds.inverter_active_powers[prod_id]
        else:
            items = ProdIds.irradiance

        # loop through each item, so that each item will have its own file
        for k, v in items.items():
            if self.stopRunning:
                break
            prod_id = {k:v}
            with ThreadPoolExecutor(max_workers=1) as executor:
                # generate output file name
                if isInv:
                    # make dir if needed
                    dir_path = Path(f"Data\\ActivePower\\{self.monthNames[int(self.month) - 1]}{self.year}\\")
                    dir_path.mkdir(parents=True, exist_ok=True)

                    invNum = v.split()[3]
                    outputFile = f"{dir_path}\\Inverter{invNum}.csv"
                    print(f'Inverter {invNum}')
                else:
                    # make dir if needed
                    dir_path = Path(f"Data\\Irradiance\\")
                    dir_path.mkdir(parents=True, exist_ok=True)

                    outputFile = f'{dir_path}\\{self.monthNames[int(self.month) - 1]}{self.year}.csv'

                future = executor.submit(multTimeInts, outputFile, self.startTimes, self.endTimes, prod_id, False)
                try:
                    result = future.result(timeout=60)
                except HTTPError:
                    print('HTTPError')
                except TimeoutError:
                    print('No data')
                except IndexError:
                    pass
            
    # return True if the given file, assumed to have data for one day for one inverter, likely has too little data
    def checkIfTooLittleData(self, filename):
        df = pd.read_csv(filename)

        # extract the HH:MM:SS of the first and last recorded times
        first_time = df.iloc[0]['Time Stamp'].split()[1]
        last_time = df.iloc[-1]['Time Stamp'].split()[1]

        first_h = int(first_time[0:2])
        first_m = int(first_time[3:5])
        last_h = int(last_time[0:2])
        last_m = int(last_time[3:5])

        # bad data if start or end times miss data
        if first_h > 5:
            return True
        if first_h == 5 and first_m > 40:
            return True
        if last_h < 21:
            return True
        
        # even if start or end times are good, there may be data missing in between
        totalMins = (last_m + (last_h * 60)) - (first_m + (first_h * 60))
        numTimesRecorded = int(totalMins / 5)
        if numTimesRecorded != df.shape[0] - 1:
            return True
        
        return False

    # determine which days likely do not have data and days that have too little data
    def findDaysWithoutData(self, start, end, prod_id, outputFile):
        noDataDays = []
        tooLittleDataDays = []
        
        # loop through every day
        for i in range(0, len(start)):
            if self.stopRunning:
                break

            print(f'{i + 1}')

            tooLong = False
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(multTimeInts, outputFile, [start[i]], [end[i]], prod_id, False)
                try:
                    result = future.result(timeout=10)
                except HTTPError:
                    tooLong = True
                    noDataDays.append(i + 1)
                    print('HTTPError')
                except TimeoutError:
                    tooLong = True
                    noDataDays.append(i + 1)
                    print('No data')

            if not tooLong and self.checkIfTooLittleData(outputFile):
                tooLittleDataDays.append(i + 1)

        if self.stopRunning:
            return []
        return [noDataDays, tooLittleDataDays]

    # get no and low data for inverters in one month
    def seeNoAndLowDataDaysInv(self, month, year, invNum=1):
        self.month = month
        self.year = year
        times = TimesGenerator.getAllTimesInMonth(month, year)
        self.startTimes = times[0]
        self.endTimes = times[1]
        key = ''
        val = ''
        if invNum == 1:
            key = '20720'
            val = "Active Power Inverter 1 (kW)"
        else:
            for k, v in ProdIds.inverter_active_powers.items():
                if v == f"Active Power Inverter {invNum} (kW)":
                    key = k
                    val = v
        prod_id = {key:val}

        res = self.findDaysWithoutData(self.startTimes, self.endTimes, prod_id, "Data_Retrieval\\TestInv.csv")
        noData = res[0]
        lowData = res[1]
        print(f'No data: {noData}')
        print(f'Low data: {lowData}')

        self.badDays = noData + lowData

    # get no and low data for irradiance in one month
    def seeNoAndLowDataDaysIrradiance(self, month, year):
        self.month = month
        self.year = year
        times = TimesGenerator.getAllTimesInMonth(month, year)
        self.startTimes = times[0]
        self.endTimes = times[1]
        prod_id = {'27986':'Plant Irradiance (GHI)'}

        res = self.findDaysWithoutData(self.startTimes, self.endTimes, prod_id, "Data_Retrieval\\TestIrr.csv")
        noData = res[0]
        lowData = res[1]
        print(f'No data: {noData}')
        print(f'Low data: {lowData}')

        self.badDays = noData + lowData

    if __name__ == '__main__':
        pass
        #seeNoAndLowDataDaysInv('05', '2025')
        #seeNoAndLowDataDaysIrradiance('05', '2025')