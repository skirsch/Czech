import csv
from datetime import datetime
import argparse

def process_vaccine_data(input_file, output_file):
  """
  Reads the large CSV file in Czech Republic format and 
  and writes the results to two output CSV files, one for male, one for female, in the buckets format.

  Args:
      input_file (str): Path to the input CSV file.
      output_file (str)
  """
  with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    out_writer = csv.writer(outfile)
    # Write header row for both output files
    out_writer.writerow(['mrn', 'Vax_code', 'Dose_number', 'Vax_date', 'Death_date', 'Vax_name', 'Birth_date'])
      
    reader = csv.reader(infile)
    for row_num, row in enumerate(reader, start=1):
      # Skip header row
      if row_num == 1:
        continue
      
      # Extract data
      mrn = str(row_num)
      sex = row[0]
      birth_year = row[1]
      if not birth_year:
        continue    # skip this record if no birth year
      death_date = row[2]

      if death_date:   # if death date present, convert the format just once, not in the loop
          try:
            death_date_obj = datetime.strptime(death_date, '%Y-%m-%d')
            death_date = death_date_obj.strftime('%m/%d/%Y')
          except ValueError:
            print(f"Error: Invalid death_date format {death_date} for row {row_num}")
            death_date = ""
      
      # Process vaccine data for each dose
      for dose_num in range(1, 8):
        vax_date = row[3 + (dose_num - 1) * 4]
        #  loop if vax_date is empty (no more doses)
        if not vax_date:
          continue    # see if any other doses since a dose can be missing so contine and don't break
        vax_code = int(row[5 + (dose_num - 1) * 4][2:])
        vax_name = row[6 + (dose_num - 1) * 4]

        # Convert date format for vax_date and death_date (if not empty)
        try:
          vax_date_obj = datetime.strptime(vax_date, '%Y-%m-%d')
          vax_date = vax_date_obj.strftime('%m/%d/%Y')
        except ValueError:
          print(f"Error: Invalid vax_date format {vax_date} for row {row_num}")
          vax_date = ""
        
        # Write an output row for each dose given
        output_row = [mrn, vax_code, dose_num, vax_date, death_date, vax_name, f"1/1/{birth_year}"]
        out_writer.writerow(output_row)

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Convert input file to buckets format.")
    parser.add_argument('in_filename', type=str, help='The input CSV file to convert to buckets format')
    # optional positional arg with default
    parser.add_argument('out_filename', type=str, help='Output filename')    
    # Parse the arguments
    args = parser.parse_args()
    
    # Call the function with the provided filename
    process_vaccine_data(args.in_filename, args.out_filename)
    
