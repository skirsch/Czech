# This is the OLD KCOR.py, the main program to generate the KCOR output for the Czechia data.
#
# This file used to be named cfr_by_week.py but now is KCOR.py. 
# 
# INSTRUCTIONS:
# 
# To generate the files: 
# 
#           cd code; make KCOR
# 
# The output file is in the data directory (specified in Makefile)
#     KCOR.xlsx

import pandas as pd
import numpy as np
from pandas import ExcelWriter
import datetime
import itertools


#
# This generates the KCOR output.
# fixed on 8/5/2025 to filter out rows with infection of 2 or more
# This is the main program to generate the KCOR output for the Czechia data.
# It is based on the vax_24.py program which does the same thing but this uses the Nov 2024 data.
# This is the main program to generate the KCOR output for the Czechia data.

# See also CMR_plots.py which is the CMR output which has additional info for KCOR and the counts should match since enroll is <=.
# 
# This code is derived from vax_24.py which analyses the official Nov 2024 Czechia data
# The idea here is to use the infected date as the index, then count deceased both if vaccinated or unvaccinated.
# infected and died_from_covid are the two key output columns
#
# Steps to make this.
# 1.  Read about the dataset here:
#     https://www.nzip.cz/data/2135-covid-19-prehled-populace which describes the fields
# 1a. Download the datafile listed below:
#     wget https://data.mzcr.cz/data/distribuce/402/Otevrena-data-NR-26-30-COVID-19-prehled-populace-2024-01.csv
# 2. rename the datafile to vax_24.csv and put in the data directory
# 3. cd code; make KCOR

# this creates cfr_by_week.csv in the data directory

# see vax_24.py for details about the database

# PURPOSE
# The purpose of this program to summarize the stats per week to compute the CFR fo9r the time period.
# Fortunately, the infected/deceased matches up infection date with death so we know # infected and died.

# Index fields:

# date of most recent infection: 
# Vaccinated at time of infection: 0 or 1 
# Vaccine brand of first shot: 
# YOB: year of birth
# boosted at time of infection: 0 or 1

# value fields
# Died or not from the infection: 0 or 1 (we need to compute this before the groupby)
# infected: 0 or 1


# value fields
# Count: number of records meeting that index
# Note can use Infected=1 in pivot to look at number infected. Shorthand for using date

# number of infections: 
# too many rows if add these and I have that data in vax_24
# Date of first vaccine: 
# Date of booster:


# So just translate the dates and compute the died or not

# all fields in Czech
# "ID","Infekce","Pohlavi","RokNarozeni","DatumPozitivity","DatumVysledku",
# "Vylecen","Umrti","Symptom","TypTestu","Datum_Prvni_davka","Datum_Druha_davka","Datum_Treti_davka","Datum_Ctvrta_davka","Datum_Pata_davka",
# "Datum_Sesta_davka","Datum_Sedma_davka","OckovaciLatkaKod_Prvni_davka","OckovaciLatkaKod_Druha_davka","OckovaciLatkaKod_Treti_davka",
# "OckovaciLatkaKod_Ctvrta_davka","OckovaciLatkaKod_Pata_davka","OckovaciLatkaKod_Sesta_davka","OckovaciLatkaKod_Sedma_davka",
# "PrimPricinaHospCOVID","bin_Hospitalizace","min_Hospitalizace","dni_Hospitalizace","max_Hospitalizace","bin_JIP","min_JIP","dni_JIP","max_JIP",
# "bin_STAN","min_STAN","dni_STAN","max_STAN","bin_Kyslik","min_Kyslik","dni_Kyslik","max_Kyslik","bin_HFNO","min_HFNO","dni_HFNO","max_HFNO",
# "bin_UPV_ECMO","min_UPV_ECMO","dni_UPV_ECMO","max_UPV_ECMO","Mutace","DatumUmrtiLPZ","Long_COVID","DCCI"

# all fields (in English)
# ID,Infection,Gender,YearOfBirth,DateOfPositiveTest,DateOfResult,Recovered,Date_COVID_death,
# Symptom,TestType,Date_FirstDose,Date_SecondDose,date_vax3Dose,Date_FourthDose,Date_FifthDose,Date_SixthDose,Date_SeventhDose,
# VaccineCode_FirstDose,VaccineCode_SecondDose,VaccineCode_ThirdDose,VaccineCode_FourthDose,VaccineCode_FifthDose,VaccineCode_SixthDose,VaccineCode_SeventhDose,PrimaryCauseHospCOVID,bin_Hospitalization,
# min_Hospitalization,days_Hospitalization,max_Hospitalization,bin_ICU,min_ICU,days_ICU,max_ICU,bin_StandardWard,min_StandardWard,days_StandardWard,max_StandardWard,bin_Oxygen,
# min_Oxygen,days_Oxygen,max_Oxygen,bin_HFNO,min_HFNO,days_HFNO,max_HFNO,bin_MechanicalVentilation_ECMO,min_MechanicalVentilation_ECMO,
# days_MechanicalVentilation_ECMO,max_MechanicalVentilation_ECMO,Mutation,DateOfDeath,Long_COVID,DCCI

# data.dtypes() to print out datatypes 
import pandas as pd

data_file='../data/vax_24.csv'
data_file='../data/sample.csv' # for debug
output_file = '../data/KCOR'

boosted='boosted_before_infected'
vaxxed='vaxxed_before_infected'
COVID_died='died_from_COVID'
infected='infected'   # positive test is a date. Don't really need this but handy for doing sums in excel
infected_and_vaxxed='infected_and_vaxxed'
COVID_died_and_vaxxed='COVID_died_and_vaxxed'
infected_and_unvaxxed='infected_and_unvaxxed'
COVID_died_and_unvaxxed='COVID_died_and_unvaxxed'

# And the value fields that I want to sum up so I can compute an IFR
# the first two will create # COVID deaths and # of ACM deaths for people in the cohort
# value_fields= ['Date_COVID_death', 'DateOfDeath']    
# this is the core list. I'll append _w1 etc to every one of these items

# just for reference. I have to process each field manually 


def main(data_file, output_file):
    # Load the CSV file into a DataFrame. 
    # I have plenty of memory so let pandas know that to avoid type errors on dose 6 which happens later in the fil

    print(f"Loading data from {data_file}")
    data = pd.read_csv(data_file, low_memory=False)
    print(f"Data loaded with {len(data)} rows and {len(data.columns)} columns")
    
    # rename the columns in English
    data.columns = [
        'ID', 'Infection', 'Gender', 'YearOfBirth', 'DateOfPositiveTest', 'DateOfResult', 'Recovered', 'Date_COVID_death',
        'Symptom', 'TestType', 'Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose',
        'Date_FifthDose', 'Date_SixthDose', 'Date_SeventhDose', 'VaccineCode_FirstDose', 'VaccineCode_SecondDose',
        'VaccineCode_ThirdDose', 'VaccineCode_FourthDose', 'VaccineCode_FifthDose', 'VaccineCode_SixthDose',
        'VaccineCode_SeventhDose', 'PrimaryCauseHospCOVID', 'bin_Hospitalization', 'min_Hospitalization',
        'days_Hospitalization', 'max_Hospitalization', 'bin_ICU', 'min_ICU', 'days_ICU', 'max_ICU', 'bin_StandardWard',
        'min_StandardWard', 'days_StandardWard', 'max_StandardWard', 'bin_Oxygen', 'min_Oxygen', 'days_Oxygen',
        'max_Oxygen', 'bin_HFNO', 'min_HFNO', 'days_HFNO', 'max_HFNO', 'bin_MechanicalVentilation_ECMO',
        'min_MechanicalVentilation_ECMO', 'days_MechanicalVentilation_ECMO', 'max_MechanicalVentilation_ECMO',
        'Mutation', 'DateOfDeath', 'Long_COVID', 'DCCI']

    # Convert all columns starting with 'Date' from ISO week format to datetime
    print(f"Converting date columns from ISO week format...")
    date_cols = [col for col in data.columns if col.startswith('Date')]
    for col in date_cols:
        print(f"  Converting {col}...")
        # Keep as pandas Timestamp for efficient comparisons (don't convert to .date)
        data[col] = pd.to_datetime(data[col] + '-1', format='%G-%V-%u', errors='coerce')
    print(f"Date conversion complete.")
    
    # if you got infected more than once, it will create a duplicate record (with a different ID) so
    # remove those records so we don't double count the deaths.

    # Remove records where Infection > 1
    data = data[(data['Infection'].fillna(0).astype(int) <= 1)]

    # Transform YearOfBirth to 4-digit integer year, missing/invalid as -1
    def parse_year(y):
        y_str = str(y)
        if len(y_str) == 1:
            return -1
        try:
            year = int(y_str[:4])
            if 1900 <= year <= datetime.datetime.now().year:
                return year
        except Exception:
            pass
        return -1
    data['YearOfBirth'] = data['YearOfBirth'].apply(parse_year).astype(int)

    # Enrollment dates: use the specified ISO week list
    enrollment_dates = ['2021-24', '2021-13', '2021-41', '2022-06', '2023-06', '2024-06']
    # enrollment_dates = ['2021-24', '2022-06']   # complete faster for testing
                        
    dose_date_cols = [
        'Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose',
        'Date_FourthDose', 'Date_FifthDose', 'Date_SixthDose'
    ]

    def iso_week_to_date(iso_week_str):
        # Expects 'YYYY-WW' format, returns pandas Timestamp for consistent comparisons
        year, week = iso_week_str.split('-')
        return pd.to_datetime(f'{year}-W{week}-1', format='%G-W%V-%u')

    # Dose dates are already pandas Timestamps from the initial conversion, no need to re-convert
    print(f"Dose dates already converted to Timestamps.")

    with ExcelWriter(output_file, engine='xlsxwriter') as writer:
        for enroll_str in enrollment_dates:
            print(f"Processing enrollment date {enroll_str} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            enroll_timestamp = iso_week_to_date(enroll_str)
            
            # Vectorized dose group assignment using boolean masks
            print(f"  Computing dose groups vectorized...")
            df = data.copy()
            
            # Create boolean masks for each dose being valid (not null and <= enrollment_date)
            dose1_valid = data['Date_FirstDose'].notna() & (data['Date_FirstDose'] <= enroll_timestamp)
            dose2_valid = data['Date_SecondDose'].notna() & (data['Date_SecondDose'] <= enroll_timestamp)
            dose3_valid = data['Date_ThirdDose'].notna() & (data['Date_ThirdDose'] <= enroll_timestamp)
            dose4_valid = data['Date_FourthDose'].notna() & (data['Date_FourthDose'] <= enroll_timestamp)
            dose5_valid = data['Date_FifthDose'].notna() & (data['Date_FifthDose'] <= enroll_timestamp)
            dose6_valid = data['Date_SixthDose'].notna() & (data['Date_SixthDose'] <= enroll_timestamp)
            
            # Start with dose group 0 for everyone
            df['dose_group'] = 0
            
            # Assign higher dose groups based on valid doses (order matters!)
            df.loc[dose1_valid, 'dose_group'] = 1
            df.loc[dose2_valid, 'dose_group'] = 2  
            df.loc[dose3_valid, 'dose_group'] = 3
            df.loc[dose4_valid, 'dose_group'] = 4
            df.loc[dose5_valid, 'dose_group'] = 5
            df.loc[dose6_valid, 'dose_group'] = 6
            
            # Cap at 5 (as in original code)
            df['dose_group'] = df['dose_group'].clip(upper=5)
            
            print(f"  Creating one-hot encoding for dose groups...")
            # One-hot encode dose_group (vectorized)
            dose_onehot = pd.get_dummies(df['dose_group'], prefix='dose')
            # Ensure all dose_0 ... dose_6 columns exist
            for i in range(7):
                colname = f'dose_{i}'
                if colname not in dose_onehot:
                    dose_onehot[colname] = 0
            # Concatenate one-hot columns
            df = pd.concat([df, dose_onehot[[f'dose_{i}' for i in range(7)]]], axis=1)
            
            print(f"  Grouping and aggregating...")
            # Group by YearOfBirth, DateOfDeath, Gender and sum dose columns (includes deaths and survivors)
            group_cols = ['YearOfBirth', 'DateOfDeath', 'Gender']
            dose_cols = [f'dose_{i}' for i in range(7)]
            # Now the magic line that does all the work
            summary = df.groupby(group_cols, dropna=False)[dose_cols].sum().reset_index()
            # Ensure YearOfBirth is integer and missing is -1
            summary['YearOfBirth'] = summary['YearOfBirth'].fillna(-1).astype(int)
            # Add Count column (sum of dose columns per row)
            summary['Count'] = summary[dose_cols].sum(axis=1)
            
            print(f"  Writing to Excel sheet...")
            # Write to Excel
            out_cols = group_cols + dose_cols + ['Count']
            summary[out_cols].to_excel(writer, sheet_name=enroll_str, index=False)
            print(f"  Completed enrollment date {enroll_str}")
            print("=" * 50)

    print(f"Output written to {output_file}")


# Entry point for command-line usage
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python KCOR.py <input_csv> <output_xlsx>")
        sys.exit(1)
    data_file = sys.argv[1]
    output_file = sys.argv[2]
    main(data_file, output_file)