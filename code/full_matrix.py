'''
This produces vaerious time series analysis I thought would be useful.

These time series are simply 1 year mortality for given vaccine dose/brand combinations.

What you really want to see is death per month for the next 12 months for each combination of date, dose, brand!

but see vax.py for the much more detailed time series outputs.

About the script:

Takes 1 argument: The source file in original Czech format
Output written to std out is a .csv file with a full matrix analysis

Example usage:
python full_matrix.py CR_records.csv >full_matrix.csv

Four different "clinical trials" are done in parallel.

Czech input file format is:
Sex, Year of Birth, Date of Death, Vax1 date, Vax1 batch code, Vax1 Code, Vax1 Name, <repeat these 4 fields for 7 vaccines>
"F",1956,,2021-05-03,"EY3014","CO01","Comirnaty",2021-06-14,"FD0168","CO01","Comirnaty",2021-12-11,"1F1020A","CO01","Com
irnaty",2022-09-29,,"CO08","Comirnaty Original/Omicron BA.1",2023-10-10,"HH0832","CO20","Comirnaty Omicron XBB.1.5.",,,,
,,,,


'''

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
# set to 3 to ignore shots given in Jan and Feb 2021

# Column names
STUDY='STUDY'
YOB='YOB'
SEX='SEX'
MONTH='MONTH'  # enrollment month in 2021 (0 if unvaxxed)
MFG1='MFG1'
MFG2='MFG2'
MFG3='MFG3'
NUM_ENROLLED='# enrolled'
NUM_DIED='# died'

# Input Field indexes
I_SEX=0
I_YOB=1
I_DOD=2
I_VD1=3
I_MFG1=5
I_VD2=I_VD1+4
I_MFG2=I_MFG1+4
I_VD3=I_VD2+4
I_MFG3=I_MFG2+4

# Vax1 date, Vax1 batch code, Vax1 Code, Vax1 Name, 
# sex
MALE="M"
FEMALE="F"
UNKNOWN="X"

# vax type and value to record in the MFG column
PFIZER="PF"     # 5586979 got shot 1
MODERNA="MO"    #  526453 got shot 1
ASTRA="AZ"      #  447450 got shot 1
JANN="JA"       #  412314 got shot 1
NOVAVAX="NOVA"  #    5425 got shot 1 but only in 2022 so doesn't appear in Study 2. 14 died. MR of just 258, but there wasn't a full year to die.

OTHER="OTHER"
UNVAX="NONE"

# Define the range of allowable values
R_STUDY = list(range(1,5))   # four studies (1 shot, 2 shot, 3 shot, unvaxxed)
R_YOB = range(1920, 2021)  # 1920 to 2020 inclusive
R_SEX = [MALE, FEMALE, UNKNOWN]
R_MONTH = list(range(0, 13))  # month in 2021 enrolled in the study. 0 means unvaxxed enrolled in 2022.
R_MFG = [PFIZER, MODERNA, ASTRA, JANN, NOVAVAX, OTHER, UNVAX]


Date=namedtuple('Date', ['month', 'day', 'year']) 

def parse_date(v_date):
    # return a structure where you can reference .month, .year as numbers. Set all components to 0 if no date
    # Note: leading spaces in the test file before the date will cause the date to be zero
    # So , 2021-22-22, has a leading space
    try:
        return datetime.strptime(v_date, "%Y-%m-%d")
    except:
        return Date(0,0,0)
    
JAN_2022=parse_date("2022-01-01")    
        
MFG_DICT = {'CO01': PFIZER, 'CO02': MODERNA, 'CO08':PFIZER, 'CO09': PFIZER, 'CO15': MODERNA, 'CO16': PFIZER, 
            'CO19': MODERNA, 'CO20': PFIZER, 'CO21':PFIZER, 'CO23':PFIZER,
             'CO03': ASTRA, 'CO04':JANN, 'CO07': NOVAVAX }
def parse_mfg(mfg):
    if not mfg:
        return UNVAX
    try:
        return MFG_DICT[mfg]
    except:
        return OTHER

def died_within_year(dod, date_of_shot):
    # if didn't die, dod is Date and date_of_shot will be a datetime object
    # so make this test here to avoid a type mismatch in the subtraction in the last line
    if dod.year==0:
        return(False)
    # compute difference in days
    days_diff = (dod - date_of_shot).days
    # Check if the death occurred within 12 months (365 days)
    return (0 <= days_diff <= 365)
        
def track_vaccine_data(filename, start_month):
    # Initialize dictionaries to keep track of counts
    # 0 index is 1920, index 100 is 2020

    # indices are [YOB, Sex, Vax type of shot 1, vax type of shot 2, month # of most recent shot]

    # How we handle the unvaccinated:
    # Don't do anything special for unvaccinated (which is just a UU) tally; just do not ignore them!!
    # however, unvaccinated must die > July 1, 2021 or not die to be considered as UU. Only deaths before July 1,2022 are counted.

    # Lists are too inefficent
    # shot_count = [[[[0 for _ in range(4)] for _ in range(4)] for _ in range(3)] for _ in range(101)]
    # can do this, but dataframes are better:
    # shot_count = np.zeros((101,3,4,4,12), dtype=int)
    # death_count = np.zeros((101,3,4,4,12), dtype=int)   # death within 1 yr of most recent shot

    # Generate all combinations of the categories. MFG is listed twice since dose 1 vs. dose 2
    combinations = list(itertools.product(R_STUDY, R_YOB, R_SEX, R_MONTH, R_MFG, R_MFG, R_MFG))

    # Create a DataFrame with MultiIndex
    index = pd.MultiIndex.from_tuples(combinations, names=[STUDY, YOB, SEX, MONTH, MFG1, MFG2, MFG3])

    # now append the two counters to use at that index location and set counters to zero
    df = pd.DataFrame(index=index, columns=[NUM_ENROLLED, NUM_DIED]).fillna(0)

    # output will iterate over the indices and output a column for each index value as well as two columns for the shot and death counts
    # so there are 6 output columns and 48 rows for each of 101 birth years, so 4848 rows x 6 columns so 29,088 cells with data

    # Open the file and read it line by line

    with open(filename, 'r') as file:
        reader = csv.reader(file)
        reader.__next__()  # bypass header

        for row in reader:
            # Extract the relevant fields from the Czech source file. Everything is read as a string.
            sex=row[I_SEX]
            sex=sex if sex !='' else UNKNOWN
            yob=int(row[I_YOB])
            if not yob in R_YOB:
                continue  # ignore the row if not in years I track
            dod=parse_date(row[I_DOD])

            vd1=parse_date(row[I_VD1])
            mfg1=parse_mfg(row[I_MFG1])
            vd2=parse_date(row[I_VD2])
            mfg2=parse_mfg(row[I_MFG2])
            vd3=parse_date(row[I_VD3])
            mfg3=parse_mfg(row[I_MFG3])
                
            # get the number of eligible shots given in 2021 which determine which studies the person is eligible for
            num_shots_2021 = sum(1 for vax_date in [vd1, vd2, vd3] if vax_date.year == 2021 and vax_date.month >=start_month)
            
            # Enrollment condition must NEVER look forward in time to determine enrollment eligibility! 
            # So we have an enroll on got first shot in 2021 to tally shot, then record death 1 year from enroll
            # And we have an enroll on got second vax in 2021 condition to tally shot, and record death 1 yr from enroll. 
            # We track the type of the first vax for this enrollment type.
            # And we have an enroll on no vax at all given in 2021, enroll on Jan 1 2022, and record death if happened in 2022
            # so that means a given record can tally to no rows, one row, or two rows!!!
            
            # simply record all 3 vaccines in the record with month
            # extend record to cover 0 as a month
            # all tallies show the vaccine count details for 3 vaccines. 

            # record month enrolled, list mfg1, mfg2, mfg3 slot values

            # STUDY #1: got shot #1 in 2021 on or after start_month. Enroll on shot #1 date. Death counted if within 1 yr from enroll
            # Record mfg of all three doses.

            if vd1.year==2021:
                df.loc[(1, yob, sex, vd1.month,mfg1, mfg2, mfg3), NUM_ENROLLED] += 1 
                if died_within_year(dod,vd1):
                     df.loc[(1, yob, sex, vd1.month, mfg1, mfg2, mfg3), NUM_DIED] += 1
             
            # STUDY #2: got shot #2 in 2021 where second shot on or after start_month. Enroll on second shot date. 
            # Death counted for 1 year from enroll. Record mfg of all 3 vax.
            if vd2.year==2021:
                df.loc[(2, yob, sex, vd2.month, mfg1, mfg2, mfg3), NUM_ENROLLED] += 1
                if died_within_year(dod,vd2):
                     df.loc[(2, yob, sex, vd2.month, mfg1, mfg2, mfg3), NUM_DIED] += 1
            
            # STUDY #3: got shot #2 in 2021 where second shot on or after start_month. Enroll on second shot date. 
            # Death counted for 1 year from enroll. Record mfg of all 3 vax.
            if vd3.year==2021:
                df.loc[(3, yob, sex, vd3.month, mfg1, mfg2, mfg3), NUM_ENROLLED] += 1 
                if died_within_year(dod,vd3):
                     df.loc[(3, yob, sex, vd3.month, mfg1, mfg2, mfg3), NUM_DIED] += 1            
            # Study #4: got no shots in 2021 and alive on Jan 1, 2022. Death counted for 1 year from enroll.
            # Show mfg of all 3 shots (usually UUU) since might have gotten all shots in 2022.
            if num_shots_2021 ==0:
                df.loc[(4, yob, sex, 0 , mfg1, mfg2, mfg3), NUM_ENROLLED] += 1 
                if died_within_year(dod, JAN_2022):
                     df.loc[(4, yob, sex, 0, mfg1, mfg2, mfg3), NUM_DIED] += 1                     
    
    # remove rows with enrollment=0 to make things more managable
    df = df[df[NUM_ENROLLED] != 0]
    # Write the compact DataFrame to CSV file
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


