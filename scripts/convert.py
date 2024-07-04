import csv
from datetime import datetime

def process_vaccine_data(input_file, male_output_file, female_output_file):
  """
  Processes a large CSV file with vaccination data, separates data by gender,
  and writes the results to two output CSV files.

  Args:
      input_file (str): Path to the input CSV file.
      male_output_file (str): Path to the output CSV file for males.
      female_output_file (str): Path to the output CSV file for females.
  """
  with open(input_file, 'r') as infile, open(male_output_file, 'w', newline='') as male_outfile, open(female_output_file, 'w', newline='') as female_outfile, open(other_output_file, 'w', newline='') as other_outfile:
    male_writer = csv.writer(male_outfile)
    female_writer = csv.writer(female_outfile)
    other_writer = csv.writer(other_outfile)
    # Write header row for both output files
    male_writer.writerow(['mrn', 'Vax_code', 'Dose_number', 'Vax_date', 'Death_date', 'Vax_name', 'Birth_date'])
    female_writer.writerow(['mrn', 'Vax_code', 'Dose_number', 'Vax_date', 'Death_date', 'Vax_name', 'Birth_date'])
    
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
          continue    # see if any other doses since a dose can be missing
        vax_code = int(row[5 + (dose_num - 1) * 4][2:])
        vax_name = row[6 + (dose_num - 1) * 4]

        # Convert date format for vax_date and death_date (if not empty)
        try:
          vax_date_obj = datetime.strptime(vax_date, '%Y-%m-%d')
          vax_date = vax_date_obj.strftime('%m/%d/%Y')
        except ValueError:
          print(f"Error: Invalid vax_date format {vax_date} for row {row_num}")
          vax_date = ""
        
        # Write output based on gender
        output_row = [mrn, vax_code, dose_num, vax_date, death_date, vax_name, f"1/1/{birth_year}"]
        if sex == 'M':
          male_writer.writerow(output_row)
        elif sex == 'F':
          female_writer.writerow(output_row)
        else:
          other_writer.writerow(output_row)

if __name__ == "__main__":
  input_file = "full.csv"
  male_output_file = "male.csv"
  female_output_file = "female.csv"
  other_output_file = "other.csv"
  process_vaccine_data(input_file, male_output_file, female_output_file)
  print("Processing complete. Output files generated!")
