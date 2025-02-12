# This code is derived from vax_24.py which analyses the official Nov 2024 Czechia data
# 
# 
# Steps:
# 1.  Read about the dataset here:
#     https://www.nzip.cz/data/2135-covid-19-prehled-populace which describes the fields
# 1a. Download the datafile listed below:
#     wget https://data.mzcr.cz/data/distribuce/402/Otevrena-data-NR-26-30-COVID-19-prehled-populace-2024-01.csv
# 2. rename the datafile to vax_24.csv and put in the data directory
# 3. cd code; make ifr
# this creates ifr.csv in the data directory

# see vax_24.py for details about the database

# PURPOSE
# The purpose of this program is just to compute the stats to do IFR calculation on the population REGARDLESS of vax status
# both before they got their vaccine as well as after they got their vaccine

# Hypothesis: IFR higher in Q2 vs. Q1 due to slower rollout in CR. Vaccines increased IFR
# For survival among age cohort, we won't see unvaxxed higher slope in COVID waves. I think the lines will get closer over time (unvaxxed will start with steeper slope).

# 
# Index fields:

# date of most recent infection: 
# COVID death date (Date_COVID_death column): date or blank 
# Vaccine brand of first shot: 
# YOB: 

# new index columns
# Date of first vaccine dose:    (so can do survival )

# new value columns (4 each w1, w2, w3, w4: prejan, alpha starting jan, delta, omicron)
# alive: is 1 if alive at start of wave; else zero, so 1 1 0 0
# ACMdied:  is 1 if dead in variant; else zero (so just one column has 1)
# COVIDdied: like ACM but for COVID. If infected in period and  Date_COVID_death is not blank (so just one column has 1)
# vaxxed: 1 if vaxxed in or before the variant, so 0 1 1 1 
# boosted: 1 if boosted in or before the variant, so 0 9 1 1 
# infected: 1 if infected in THAT variant; else 0 so 1 column has 1




# do not need for now
# Number of vaccines: 0-N
# Number of Infections:  
# Month and year of infection: date of positive test result
# Died within x weeks of infection:  
# Died within x weeks of most recent vaccination: blank if didn't die  



# all we need is the record count for the index fields.

# Then from the dataset in excel, use pivot table to compute IFR of ENTIRE cohort in the months before the vaccine rollouts vs. after
# The vaccination status also allows us to compute IFR of vaxxed and unvaxxed, but the meat of the analysis is the
# BEFORE vs. AFTER IFR of the FULL cohort since that eliminates selection bias.
# The reason for the vaccine breakout is simply to show people that immediately after vaccination the IFR's are different for the 
# vaxxed and unvaxxed, but if the FULL COHORT IFR didn't drop, the vaccine didn't work: the IFR differences were a mirage.

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
# Symptom,TestType,Date_FirstDose,Date_SecondDose,Date_ThirdDose,Date_FourthDose,Date_FifthDose,Date_SixthDose,Date_SeventhDose,
# VaccineCode_FirstDose,VaccineCode_SecondDose,VaccineCode_ThirdDose,VaccineCode_FourthDose,VaccineCode_FifthDose,VaccineCode_SixthDose,VaccineCode_SeventhDose,PrimaryCauseHospCOVID,bin_Hospitalization,
# min_Hospitalization,days_Hospitalization,max_Hospitalization,bin_ICU,min_ICU,days_ICU,max_ICU,bin_StandardWard,min_StandardWard,days_StandardWard,max_StandardWard,bin_Oxygen,
# min_Oxygen,days_Oxygen,max_Oxygen,bin_HFNO,min_HFNO,days_HFNO,max_HFNO,bin_MechanicalVentilation_ECMO,min_MechanicalVentilation_ECMO,
# days_MechanicalVentilation_ECMO,max_MechanicalVentilation_ECMO,Mutation,DateOfDeath,Long_COVID,DCCI

# data.dtypes() to print out datatypes 
import pandas as pd

data_file='../data/vax_24.csv'
data_file='../data/vax_24_head20k.csv' # for debug
output_file = '../data/ifr.csv'

waves=['w1', 'w2','w3', 'w4']
wave_dict={'w1':'FirstDose','d2':'SecondDose', 'd3':'ThirdDose'}

def main(data_file, output_file):
    # Load the CSV file into a DataFrame. 
    # I have plenty of memory so let pandas know that to avoid type errors on dose 6 which happens later in the file
    data = pd.read_csv(data_file, low_memory=False)

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

# date of most recent infection: 


    # Define the index fields
    index_fields = ['YearOfBirth', 'VaccineCode_FirstDose',  'DateOfPositiveTest']
    # And the value fields that I want to sum up so I can compute an IFR
    value_fields= ['Date_COVID_death', 'DateOfDeath']    

    # Transform YearOfBirth to extract the first year as an integer, handling missing or invalid entries
    data['YearOfBirth'] = data['YearOfBirth'].str.split('-').str[0].replace('', None).dropna().astype('Int32')

    # Transform the VaccineCode columns to clean then up
    # remove leading and trailing spaces, convert to uppercase so can be found in dictionary
    brand_cols=['VaccineCode_FirstDose']
    for col in brand_cols:
        data[col] = data[col].str.strip().str.upper()

    # Ensure Infection is an integer (empty=0)
    # data['Infection'] = data['Infection'].fillna(0).astype('Int32')

    # Convert dates from YYYY-WW format to pandas datetime format
    for col in ['Date_COVID_death', 'DateOfPositiveTest', 'DateOfDeath']:
        data[col] = pd.to_datetime(data[col] + '-1', format='%G-%V-%u', errors='coerce').dt.date
    # the dt.date will remove the time part of the date so things are cleaner. The  ISO format adds the time.
    # %G-%V-%u because the Czech data uses ISO 8601 weeks
    # format='%Y-%W-%w' was incorrect

    # Create 'died_in_NCmonth' column for deaths between May 30, 2021, and Oct 12, 2021 (inclusive)
    # data['died_in_NCmonth_2021'] = data['DateOfDeath'].apply(lambda x: 1 if pd.notna(x) and pd.Timestamp('2021-05-30') <= x <= pd.Timestamp('2021-10-12') else 0)
    # data['died_in_NCmonth_2022'] = data['DateOfDeath'].apply(lambda x: 1 if pd.notna(x) and pd.Timestamp('2022-05-10') <= x <= pd.Timestamp('2022-07-10') else 0)
    
    #  Drop rows without a first dose. We need to count everyone who got a dose, dead or alive. We gave unvaxxed people a "PLACEBO" does in Jan 2022.
    # data = data.dropna(subset=['Date_FirstDose'])

    # groupby only summarizes fields with values so ensure that the Code fields have a value "NONE"
    # add date of positive test so can look at mortality of those without a positive test!
    # only fill fields in the index, not in value
    maybe_empty_fields=['VaccineCode_FirstDose', 'DateOfPositiveTest']
    data[maybe_empty_fields] = data[maybe_empty_fields].fillna('NONE')

    # Perform group_by with aggregation. This does all the heavy lifting!
    # summary_df = data.groupby(index_fields).size().reset_index(name="Count")

    # setting false allows this code to count dates and sum numeric columns 
    # use sum() for adding numeric value fields
    summary_df = data.groupby(index_fields)[value_fields].count().reset_index() 
    summary_df['Count'] = data.groupby(index_fields).size().values

    
    # now modify the labels to be more user friendly
    from mfg_codes import MFG_DICT

    # Transform VaccineCode_xxxDose using the dictionary so have friendly names.
    doses=['d1']
    dose_dict={'d1':'FirstDose','d2':'SecondDose', 'd3':'ThirdDose'}
    
    for d in doses:
        summary_df['VaccineCode_'+dose_dict[d]] = summary_df['VaccineCode_'+dose_dict[d]].map(MFG_DICT) 

    # Now switch back NONE to empty since we used NONE as a placeholder everywhere
    summary_df.replace('NONE', '', inplace=True)

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