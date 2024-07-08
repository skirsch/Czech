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

# Fields
SEX=0
YOB=1
DOD=2
VD1=3
VC1=5
VD2=7
VC2=9
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

# Define the ranges and categories
YOB = range(1920, 2021)  # 1920 to 2020 inclusive
SEX = [MALE, FEMALE, UNKNOWN]
MFG = [PFIZER, MODERNA, OTHER, UNVAX]
MONTH = list(range(1, 13))  # month of most recent shot

Date=namedtuple('Date', ['month', 'day', 'year']) 

def parse_date(v_date):
    # return a structure where you can reference .month, .year as numbers. Set all components to 0 if no date
    try:
        return datetime.strptime(v_date, "%m/%d/%Y")
    except:
        return Date(0,0,0)
        

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
    index = pd.MultiIndex.from_tuples(combinations, names=['yob', 'sex', 'mfg1', 'mfg2', 'month'])
    df = pd.DataFrame(index=index, columns=['# shot', '# died']).fillna(0)

    # Example increment: df.loc[(2011, 'M', 'b', ....), '# shot'] += 1

    # output will iterate over the indices and output a column for each index value as well as two columns for the shot and death counts
    # so there are 6 output columns and 48 rows for each of 101 birth years, so 4848 rows x 6 columns so 29,088 cells with data

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        reader.__next__()  # bypass header
        for row in reader:
            # Extract the relevant fields from the Czech source file. Everything is read as a string.
            # x = 3 if y == 1 else 4    # to set value to 3 or 4 based on y
            sex=row[SEX]
            sex=sex if sex is not None else UNKNOWN
            yob=int(row[YOB])
            dod=parse_date(row[DOD])
            vd1=parse_date(row[VD1])
            vc1=parse_mfg(row[VC1])
            vd2=parse_date(row[VD2])
            vc2=parse_mfg(row[VC2])
            try:
                
                month = v_date.month
                # check to see if the record qualifies to be tallied befreo doing any tallying!
                if month<start_month:
                        continue    # ignore this record and go to the next if not in scope
                # Parse the birth year
                birth_year = int(datetime.strptime(birth_year_str, "%m/%d/%Y").year)

                # count the number of doses
                birth_year_counts[birth_year] += 1
                monthly_vaccine_counts[birth_year][month] += 1

                if death_date_str:
                    # Parse the death date
                    death_date = datetime.strptime(death_date_str, "%m/%d/%Y")
                    
                    # Calculate the difference in days
                    days_diff = (death_date - vaccine_date).days

                    # Check if the death occurred within 12 months (365 days)
                    if 0 <= days_diff <= 365:
                        death_within_12_months_counts[birth_year] += 1
            except ValueError:
                # Handle the case where the date format is incorrect
                print(f"Invalid date format in line: {row}", file=sys.stderr)

    # Write the results to standard output in CSV format
    
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


