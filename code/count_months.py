import argparse
from collections import Counter
import csv
from datetime import datetime

def count_months(filename, in_year):
    # Initialize a Counter object to keep track of month counts
    month_counts = Counter()

    # Open the file and read it line by line
    with open(filename, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            # Extract the date field (4th field)
            date_str = row[3]
            if date_str:
                try:
                    # Parse the date
                    date = datetime.strptime(date_str, "%m/%d/%Y")
                    # Extract the year to make sure it matches
                    year = date.year
                    if not year == in_year:
                        continue    # skip this row. Wrong year.
                    # Extract the month
                    month = date.month
                    # Increment the count for this month
                    month_counts[month] += 1
                except ValueError:
                    # Handle the case where the date format is incorrect
                    print(f"Invalid date format: {date_str}")

    # Print the counts for each month
    for month in range(1, 13):
        print(f"Month {month:02}: {month_counts[month]} entries")

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Count entries for each month in a CSV file.")
    parser.add_argument('filename', type=str, help='The CSV file to process')
    parser.add_argument('year', type=str, help='The year to calculate vax administration counts by month')
    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with the provided filename and desired year
    count_months(args.filename, args.year)
