# Steps:
# 1. Download the datafile listed below:
#     wget https://data.mzcr.cz/data/distribuce/402/Otevrena-data-NR-26-30-COVID-19-prehled-populace-2024-01.csv
# 2. rename the datafile to vax_24.csv and put in the data directory
# 3. cd code; make vax_24
# this creates vax_24_summary.csv in the data directory


# new vax record level data released in Nov 2024
# Hence the filename vax_24.py for the analysis of the 2024 Czech Republic data

# Data file: https://www.nzip.cz/data/2135-covid-19-prehled-populace
#
# written about here: https://smis-lab.cz/2024/11/07/dalsi-velka-datova-sada-uzis-zverejnena/

# Notes:
# DCCI is non-zero only if infected
# Date of death ranges from 2020-10 to 2024-41 (using wk number format)

# all fields (in English)
# ID,Infection,Gender,YearOfBirth,DateOfPositiveTest,DateOfResult,Recovered,Deceased,Symptom,TestType,Date_FirstDose,Date_SecondDose,Date_ThirdDose,Date_FourthDose,Date_FifthDose,Date_SixthDose,Date_SeventhDose,
# VaccineCode_FirstDose,VaccineCode_SecondDose,VaccineCode_ThirdDose,VaccineCode_FourthDose,VaccineCode_FifthDose,VaccineCode_SixthDose,VaccineCode_SeventhDose,PrimaryCauseHospCOVID,bin_Hospitalization,min_Hospitalization,days_Hospitalization,max_Hospitalization,bin_ICU,min_ICU,days_ICU,max_ICU,bin_StandardWard,min_StandardWard,days_StandardWard,max_StandardWard,bin_Oxygen,min_Oxygen,days_Oxygen,max_Oxygen,bin_HFNO,min_HFNO,days_HFNO,max_HFNO,bin_MechanicalVentilation_ECMO,min_MechanicalVentilation_ECMO,
# days_MechanicalVentilation_ECMO,max_MechanicalVentilation_ECMO,Mutation,DateOfDeath,Long_COVID,DCCI

# index: YearOfBirth, VaccineCode_FirstDose, Date_FirstDose, Infection, DCCI, 
# value: # records, died in 30, 60, 90, 120, 150, 180, etc. of shot till 360 using the DateOfDeathLPZ

# data.dtypes() to print out datatypes
import pandas as pd

data_file='../data/vax_24.csv'
# data_file='../data/sample.csv'
output_file = '../data/vax_24_summary.csv'


def main(data_file, output_file):
    # Load the CSV file into a DataFrame. 
    # I have plenty of memory so let pandas know that to avoid type errors on dose 6 which happens later in the file
    data = pd.read_csv(data_file, low_memory=False)

    # rename the columns in English
    data.columns = [
        'ID', 'Infection', 'Gender', 'YearOfBirth', 'DateOfPositiveTest', 'DateOfResult', 'Recovered', 'Deceased',
        'Symptom', 'TestType', 'Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose',
        'Date_FifthDose', 'Date_SixthDose', 'Date_SeventhDose', 'VaccineCode_FirstDose', 'VaccineCode_SecondDose',
        'VaccineCode_ThirdDose', 'VaccineCode_FourthDose', 'VaccineCode_FifthDose', 'VaccineCode_SixthDose',
        'VaccineCode_SeventhDose', 'PrimaryCauseHospCOVID', 'bin_Hospitalization', 'min_Hospitalization',
        'days_Hospitalization', 'max_Hospitalization', 'bin_ICU', 'min_ICU', 'days_ICU', 'max_ICU', 'bin_StandardWard',
        'min_StandardWard', 'days_StandardWard', 'max_StandardWard', 'bin_Oxygen', 'min_Oxygen', 'days_Oxygen',
        'max_Oxygen', 'bin_HFNO', 'min_HFNO', 'days_HFNO', 'max_HFNO', 'bin_MechanicalVentilation_ECMO',
        'min_MechanicalVentilation_ECMO', 'days_MechanicalVentilation_ECMO', 'max_MechanicalVentilation_ECMO',
        'Mutation', 'DateOfDeath', 'Long_COVID', 'DCCI']


    # Define the index and value fields
    index_fields = ['YearOfBirth', 'VaccineCode_FirstDose', 'VaccineCode_SecondDose', 'VaccineCode_ThirdDose', 'Date_FirstDose', 'Infection', 'DCCI']
    # list here the ones to output even though all are generated for all 3 doses
    value_fields = ['Countd1', 'Died_30d1', 'Died_60d1', 'Died_90d1', 'Died_180d1', 'Died_270d1', 'Died_360d1',
                    'Died_450d1', 'Died_540d1', 'Died_630d1', 'Died_720d1', 
                    'Countd2', 'Died_90d2', 'Died_180d2', 'Died_270d2', 'Died_360d2', 
                    'Countd3', 'Died_90d3', 'Died_180d3', 'Died_270d3', 'Died_360d3',
                    'died_in_NCmonth_2021', 'died_in_NCmonth_2022']  # this is set if the person died in a low COVID month

    # Transform YearOfBirth to extract the first year as an integer, handling missing or invalid entries
    data['YearOfBirth'] = data['YearOfBirth'].str.split('-').str[0].replace('', None).dropna().astype('Int32')

    # Transform the VaccineCode columns to clean then up
    # remove leading and trailing spaces, convert to uppercase so can be found in dictionary
    brand_cols=['VaccineCode_FirstDose', 'VaccineCode_SecondDose', 'VaccineCode_ThirdDose']
    for col in brand_cols:
        data[col] = data[col].str.strip().str.upper()

    # Ensure Infection is an integer (empty=0)
    data['Infection'] = data['Infection'].fillna(0).astype('Int32')

    # Convert dates from YYYY-WW format to pandas datetime format
    for col in ['Date_FirstDose', 'Date_SecondDose','Date_ThirdDose', 'DateOfDeath']:
        data[col] = pd.to_datetime(data[col] + '-1', format='%Y-%W-%w', errors='coerce')

    # For rows with no doses and death date >= 2022-01, set Date_FirstDose 
    # and VaccineCode_FirstDose to 2022 to avoid the effect where in 2021, people more 
    # likely to die or be vaccined, so gets around the strong pull of the vaccine for all 
    # alive people.


    # unvaxxed alive on Jan 1, 2022 and if no dose dates and EITHER you died after 2022 *OR* you didn't die at all.
    # this avoids picking people who were unvaxxed because they died before they could get their vaccine
    # which artificially increases deaths in the unvaccinated (think EVERYONE wanted to be vaxxed and you only didn't get 
    # vaxxed if you died.)
    data.loc[
    data[['Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose']].isna().all(axis=1) & 
        (data['DateOfDeath'].fillna(pd.Timestamp('2099-01-01')) > '2022-01-01'),
        ['Date_FirstDose', 'VaccineCode_FirstDose']] = ['2022-01-01', 'PLACEBO']

    # Create 'died_in_NCmonth' column for deaths between May 30, 2021, and Oct 12, 2021 (inclusive)
    data['died_in_NCmonth_2021'] = data['DateOfDeath'].apply(lambda x: 1 if pd.notna(x) and pd.Timestamp('2021-05-30') <= x <= pd.Timestamp('2021-10-12') else 0)
    data['died_in_NCmonth_2022'] = data['DateOfDeath'].apply(lambda x: 1 if pd.notna(x) and pd.Timestamp('2022-05-10') <= x <= pd.Timestamp('2022-07-10') else 0)
    
    #  Drop rows without a first dose. We need to count everyone who got a dose, dead or alive. We gave unvaxxed people a "PLACEBO" does in Jan 2022.
    data = data.dropna(subset=['Date_FirstDose'])

    doses=['d1', 'd2','d3']
    dose_dict={'d1':'FirstDose','d2':'SecondDose', 'd3':'ThirdDose'}
    # generates all these but outputs only those items listed above in value_fields
    day_list=[30, 60, 90,180,270,360,450,540,630,720]  

    # Compute days till death (dtd) and convert to int32. do for each dose.
    # also create count for each dose
    # Original code: 
    #   data['dtd'] = (data['DateOfDeath'] - data['Date_FirstDose']).dt.days.astype('Int32')
    for d in doses:
        data['dt'+d] = (data['DateOfDeath'] - data['Date_'+dose_dict[d]]).dt.days.astype('Int32')
        data['Count'+d] = data['Date_'+dose_dict[d]].notna().astype(int)  # Count for each dose

    # Compute the Died_xxdx fields using the dtdx column
    # make sure that x >=0  so that people can't be vaccinated after they die
    for d in doses:
        for day in day_list:
            data['Died_'+str(day)+d] = data['dt'+d].apply(lambda x: 1 if pd.notna(x) and x >= 0 and x <= day else 0)

    # effectively creates lines like these
    # data['Died_180d1'] = data['dtd1'].apply(lambda x: 1 if pd.notna(x) and x <= 180 else 0)

    # groupby only summarizes fields with values so ensure that the Code fields have a value "NONE"
    VaccineCode_fields=['VaccineCode_SecondDose', 'VaccineCode_ThirdDose']
    data[VaccineCode_fields] = data[VaccineCode_fields].fillna('NONE')

    # Perform group_by with aggregation. This does all the heavy lifting!
    summary_df = data.groupby(index_fields)[value_fields].sum().reset_index()

    # now modify the labels to be more user friendly
    from mfg_codes import MFG_DICT

    # Transform VaccineCode_xxxDose using the dictionary so have friendly names.
    for d in doses:
        summary_df['VaccineCode_'+dose_dict[d]] = summary_df['VaccineCode_'+dose_dict[d]].map(MFG_DICT) 

    # Write the summary DataFrame to a CSV file
    summary_df.to_csv(output_file, index=False)

    print(f"Summary file has been written to {output_file}.")


import sys

# Check for command-line arguments
if len(sys.argv) != 3:
    print("Usage: python script.py <source_file> <output_file>")
    sys.exit(1)

# Command-line arguments
data_file = sys.argv[1]
output_file = sys.argv[2]

main(data_file, output_file)