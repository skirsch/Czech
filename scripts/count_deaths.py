# this takes a .csv file in buckets format and tallies dose and death counts by age
# so if you want to look at Moderna vs. pfizer, create separate input files for each vaccine type, then call this
# function.

import argparse
import csv
from datetime import datetime
from collections import defaultdict
import sys

def track_vaccine_data(filename):
    # Initialize dictionaries to keep track of counts
    birth_year_counts = defaultdict(int)
    death_within_12_months_counts = defaultdict(int)
    monthly_vaccine_counts = defaultdict(lambda: defaultdict(int))

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Extract the relevant fields
            vaccine_date_str = row[3]
            death_date_str = row[4]
            birth_year_str = row[6]

            try:
                # Parse the birth year
                birth_year = int(datetime.strptime(birth_year_str, "%m/%d/%Y").year)
                birth_year_counts[birth_year] += 1

                if vaccine_date_str:
                    # Parse the vaccine date
                    vaccine_date = datetime.strptime(vaccine_date_str, "%m/%d/%Y")
                    month = vaccine_date.month
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
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with the provided filename
    track_vaccine_data(args.filename)


