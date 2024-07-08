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

where dose1_type and dose2_type are from:
0=no vax
1=pfizer
2=moderna
3=other vax
'''
#temporary till finish coding so make is happy
print("done")
exit()


import argparse
import csv
from datetime import datetime
from collections import defaultdict
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
MALE=0
FEMALE=1
OTHER=2

# vax type
PFIZER=0
MODERNA=1
OTHER=2
UNVAX=3


def track_vaccine_data(filename, start_month):
    # Initialize dictionaries to keep track of counts
    # 0 index is 1920, index 100 is 2020
    # indices are [YOB][Sex][Vax type of shot 1][vax type of shot 2]
    # where YOB 0 is 1920, 100=2020, Sex is 0-3, and the vax types range from 0 to 3
    shot_count = [[[[0 for _ in range(4)] for _ in range(4)] for _ in range(3)] for _ in range(101)]
    death_count = [[[[0 for _ in range(4)] for _ in range(4)] for _ in range(3)] for _ in range(101)]

    # output will iterate over the indices and output a column for each index value as well as two columns for the shot and death counts
    # so there are 6 output columns and 48 rows for each of 101 birth years, so 4848 rows x 6 columns so 29,088 cells with data

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for col in reader:
            # Extract the relevant fields
            sex=col[SEX]
            yob=col[YOB]
            dod=col[DOD]
            vd1=col[VD1]
            vc1=col[VC1]
            vd2=col[VD2]
            vc2=col[VC2]
            try:
                # Parse the vaccine date
                vaccine_date = datetime.strptime(vaccine_date_str, "%m/%d/%Y")
                month = vaccine_date.month
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
    writer = csv.writer(sys.stdout)
    header = ['Year of Birth', 'Number of People', 'Died Within 1 Year'] + \
             ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    writer.writerow(header)

    for year in sorted(birth_year_counts.keys()):
        row = [year, birth_year_counts[year], death_within_12_months_counts[year]]
        row += [monthly_vaccine_counts[year][month] for month in range(1, 13)]
        writer.writerow(row)

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


