'''

Takes 1 argument: The source file in original Czech format
Output written to std out is a .csv file with a full matrix analysis

Example usage:
python full_matrix.py CR_records.csv >full_matrix.csv

For each record, it will increment at least one counter and 
a second counter if the person died within 1 year of last shot.
YOB=year of birth

shots[YOB][dose1_type][dose2_type]+=1  # increment shot count for 
deaths[YOB][dose1_type][dose2_type]+=1  # count number died within 1 year of last shot date

Czech file format is:
Sex, Year of Birth, Date of Death, Vax1 date, Vax1 batch code, Vax1 Code, Vax1 Name, <repeat these 4 fields for 7 vaccines>
"F",1956,,2021-05-03,"EY3014","CO01","Comirnaty",2021-06-14,"FD0168","CO01","Comirnaty",2021-12-11,"1F1020A","CO01","Com
irnaty",2022-09-29,,"CO08","Comirnaty Original/Omicron BA.1",2023-10-10,"HH0832","CO20","Comirnaty Omicron XBB.1.5.",,,,
,,,,


'''
#temporary till finish coding so make is happy
print("done")
exit()

# import numpy as np
import pandas as pd
import itertools
import argparse
import csv
from datetime import datetime
from collections import defaultdict, namedtuple
import sys

# start_month is minimum month number for row to be processed
# set to 1 to get everything.
# set to 3 to ignore Jan and Feb

# Column names
YOB='YOB'
SEX='SEX'
MFG1='MFG1'
MFG2='MFG2'
MONTH='MONTH'
NUM_SHOT='# shot'
NUM_DIED='# died'

# Input Field indexes
I_SEX=0
I_YOB=1
I_DOD=2
I_VD1=3
I_MFG1=5
I_VD2=7
I_MFG2=9

# Vax1 date, Vax1 batch code, Vax1 Code, Vax1 Name, 
# sex
MALE="M"
FEMALE="F"
UNKNOWN="X"

# vax type
PFIZER="P"
MODERNA="M"
OTHER="O"
UNVAX="U"

# Define the range of allowable values
R_YOB = range(1920, 2021)  # 1920 to 2020 inclusive
R_SEX = [MALE, FEMALE, UNKNOWN]
R_MFG = [PFIZER, MODERNA, OTHER, UNVAX]
R_MONTH = list(range(1, 13))  # month of most recent shot

Date=namedtuple('Date', ['month', 'day', 'year']) 

def parse_date(v_date):
    # return a structure where you can reference .month, .year as numbers. Set all components to 0 if no date
    try:
        return datetime.strptime(v_date, "%m/%d/%Y")
    except:
        return Date(0,0,0)
        
MFG_DICT = '{'CO01': PFIZER, 'CO02': MODERNA, 'CO21':PFIZER}'
def parse_mfg(mfg):
    if not mfg:
        return UNVAX
    try:
        return MFG_DICT[mfg]
    except:
        return OTHER

def track_vaccine_data(filename, start_month):
    # Initialize dictionaries to keep track of counts
    # 0 index is 1920, index 100 is 2020

    # indices are [YOB, Sex, Vax type of shot 1, vax type of shot 2, month # of most recent shot]

    # Lists are too inefficent
    # shot_count = [[[[0 for _ in range(4)] for _ in range(4)] for _ in range(3)] for _ in range(101)]
    # can do this, but dataframes are better:
    # shot_count = np.zeros((101,3,4,4,12), dtype=int)
    # death_count = np.zeros((101,3,4,4,12), dtype=int)   # death within 1 yr of most recent shot


    # Generate all combinations of the categories. MFG is listed twice since dose 1 vs. dose 2
    combinations = list(itertools.product(YOB, SEX, MFG, MFG, MONTH))

    # Create a DataFrame with MultiIndex
    index = pd.MultiIndex.from_tuples(combinations, names=[YOB, SEX, MFG1, MFG2, MONTH])
    df = pd.DataFrame(index=index, columns=[NUM_SHOT, NUM_DIED]).fillna(0)

    # Example increment: df.loc[(2011, 'M', 'b', ....), '# shot'] += 1

    # output will iterate over the indices and output a column for each index value as well as two columns for the shot and death counts
    # so there are 6 output columns and 48 rows for each of 101 birth years, so 4848 rows x 6 columns so 29,088 cells with data

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        reader.__next__()  # bypass header
        for row in reader:
            # Extract the relevant fields from the Czech source file. Everything is read as a string.

            sex=row[I_SEX]
            sex=sex if sex is not None else UNKNOWN
            yob=int(row[I_YOB])
            dod=parse_date(row[I_DOD])
            vd1=parse_date(row[I_VD1])
            mfg1=parse_mfg(row[I_MFG1])
            vd2=parse_date(row[I_VD2])
            mfg2=parse_mfg(row[I_MFG2])
                
            # get month of most recent shot
            month = max(vd1.month, vd2.month)   
            
            
            # if not vaccinated for dose 1 or dose 2 or most recent dose month is less than start_month, ignore the record
            if not month or month<start_month:
                continue

            # now tally to the dose counter
            df.loc[(yob, sex, mfg1, mfg2, month), NUM_SHOT] += 1

            # if the person didn't die, we're done.
            if not dod.year:
                continue
            
            # now tally to the death counter if died within 1 year of dose
            date_of_vax=vd2 if vd2.year else vd1
            # Calculate the difference in days
            days_diff = (dod - date_of_vax).days

            # Check if the death occurred within 12 months (365 days)
            if 0 <= days_diff <= 365:
                df.loc[(yob, sex, mfg1, mfg2, month), NUM_SHOT] += 1

    # Write DataFrame to CSV
    df.to_csv(sys.stdout)

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Track vaccine data and deaths within 1 year.")
    parser.add_argument('filename', type=str, help='The CSV file to process')
    # optional positional arg with default
    parser.add_argument('start_month', nargs='?', default=1, type=int, help='Min vax month to process')    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with the provided filename
    track_vaccine_data(args.filename, args.start_month)


