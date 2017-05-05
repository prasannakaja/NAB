import sys
import random
import time
import optparse
import csv
import urllib.request as urequest
from urllib.error import HTTPError
import openpyxl

class NationalAustralianBank:
    def __init__(self, infile):
        self.postcodes_file = infile
        self.URL  = "https://api.nab.com.au/info/nab/location/locationType/atm+brc/queryType/addr/%s/5/50/1000/1/100?v=1"
        
        self.atm_file = "ATMS.csv"
        self.branch_file = "BRANCHES.csv"
        self.missed_postcodes_file = open("ERROR_POSTCODES.txt", "w")

        self.branch_headers = ['id', 'key', 'siteName', 'address1', 'address2', 'address3', 'hasCoinSwap', 'postcode', 
                            'openWeekends', 'hasQuickChange', 'bbc', 'state', 'latitude', 'isRural', 'description', 
                            'internetBank', 'foreignCurrency', 'suburb', 'bsb', 'mobileBanker', 
                            'hasIntelligentDeposit', 'longitude', 'financialPlanner',  'expressBusinessDeposit']

        self.atm_headers = ['id', 'key', 'source', 'description', 'isDeposit', 'state', 'address1', 'address2', 'address3', 
                        'address4', 'address5', 'postcode', 'location', 'suburb', 'latitude', 'longitude']

        self.ATMS =  {}
        self.BRANCHES = {}

    def write_into_csv(self, loc_details=[], itype='atm', mode='w'):
        """
            WRITE ATMS/BRANCHES DETAILS INTO CSV FILE. 
        """ 
 
        if itype=="brc":
            csvfile_name = self.branch_file
            headers = self.branch_headers
        else:
            csvfile_name = self.atm_file
            headers = self.atm_headers

        with open(csvfile_name, mode, newline='') as csvfile:
            locwriter = csv.writer(csvfile, delimiter=',', quoting=csv.QUOTE_ALL)
            if mode=='w':
                locwriter.writerow(headers) 

            for loc in loc_details:
                locwriter.writerow(loc)

    def read_postcodes(self):
        """
            READ POST CODES DATA FROM INPUT FILE.
        """
        if ".xls" in self.postcodes_file:
            wb = openpyxl.load_workbook(self.postcodes_file)
            sheet = wb.get_sheet_by_name('Sheet1')
            postcodes = []
            for row in sheet.values:
                if "postcode" in str(row[0]): continue
                postcodes.append(str(row[0]).strip())
        else:
            postcodes  = [str(i.strip()) for i in open(self.postcodes_file).readlines() if i.strip()]

        return postcodes

    def get_item_details(self, item, headers):
        atm_branch = []
        for header in headers:
            atm_branch.append(item.get(header, ''))

        return atm_branch
 
    def process_response_data(self, response):
        """
            GET ATM BRANCHES DATA.
        """
        response = response.replace('false', "'false'")
        response = response.replace('true', "'true'")
        response = eval(response)
        locations = response["locationSearchResponse"]["locations"]

        atms = []
        branches = []

        for loc in locations:
            loc_type = loc["apiStructType"]

            if loc_type=="atm":
                atm_dict = loc["atm"]
                atm = self.get_item_details(atm_dict, self.atm_headers)
                self.ATMS[atm[0]] = atm

            elif loc_type=="brc":
                branch_dict = loc["brc"]
                brc = self.get_item_details(branch_dict, self.branch_headers)
                self.BRANCHES[brc[0]] = brc


    def get_url_response(self, postcode):
        purl = urequest.Request(self.URL %postcode)


        retries = 0
        while True:

            try:
                if retries>3:
                    self.missed_postcodes_file.write("%s\n" %postcode)
                    break

                retries += 1

                ## ADD HEADERS
                purl.add_header("Host", "api.nab.com.au")
                purl.add_header("Referer", "https://www.nab.com.au/locations?return")
                purl.add_header("Content-Type", "application/json")
                purl.add_header("Accept-Encoding", "gzip, deflate")
                purl.add_header("x-nab-key", "a8469c09-22f8-45c1-a0aa-4178438481ef")

                response_data = urequest.urlopen(purl).read().decode('utf8')
                print(self.URL %postcode)

            except HTTPError as e:
                time.sleep(random.randint(8,20))

            else:            
                self.process_response_data(response_data)
                break

    def scrape_data(self):
        """
        SCRAPE ATM BRANCHES DATA
        """
        ## OPEN EMPTY CSV FILE
        self.write_into_csv()
        
        ## READ POSTCODES
        postcodes = self.read_postcodes()

        for i, postcode in enumerate(postcodes):
            print("Postcode index: %s" %str(i+1))

            sleeptime = round(random.uniform(0.5, 1.0), 2)
            time.sleep(sleeptime)
           
            self.get_url_response(postcode)

         
        ## WRITE DATA INTO CSV FILES
        atms = [v for k, v in self.ATMS.items()]
        if atms:
            self.write_into_csv(atms, 'atm')

        branches = [v for k, v in self.BRANCHES.items()]
        if branches:
            self.write_into_csv(branches, 'brc')

def main(options): 
    """
        MAIN 
    """
    input_file = options.input_file

    if input_file:
        atmObj = NationalAustralianBank(input_file)
        atmObj.scrape_data()

    else:
        print(""" Please provide "postcodes text file"  and  
                    "csv file name" to which you want to write output. 

                    script usage is below:

                 python <sciptname> -i<lat-long file> -o<name for csv file> 
        """)
        sys.exit(1)
        

if __name__=='__main__':
  
    usage = "usage: program.py -i <lat-longs file name> -o <desired csv filename>" 
    parser = optparse.OptionParser(usage=usage) 
    
    parser.add_option('-i', '--input-file',  help="Please provide latlongs.txt file")

    (options, args) = parser.parse_args()

    main(options)
 

