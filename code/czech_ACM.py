# This code is derived from cfr_by_week.
# this code enables me to plot deaths by week for each 5 year age group
# so i can compare with the US monthly UCOD death rate to see if we have a similar effect
# but this database is limited to 2020 forward.
#
# Pivot by vaccination date, first vaccine type, and whether they died from COVID.
# 
# 
# Index fields:
# YOB: 
# DOD:
# Date of first vaccine dose:  
# Vaccine brand of first shot: 
# Died from COVID (1 if died from COVID)

# value fields:
# none, just the count

# all we need is the record count for the index fields.


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
data_file='../data/sample.csv' # for debug
output_file = '../data/cfr_by_week.csv'

COVID_died='died_from_COVID' # 1 or 0

 # Define the index field and value fields
index_fields = ['YearOfBirth', 'VaccineCode_FirstDose', 'DateOfDeath', 'Date_FirstDose', COVID_died]   
value_fields= []

# And the value fields that I want to sum up so I can compute an IFR
# the first two will create # COVID deaths and # of ACM deaths for people in the cohort
# value_fields= ['Date_COVID_death', 'DateOfDeath']    
# this is the core list. I'll append _w1 etc to every one of these items

# just for reference. I have to process each field manually 


import itertools

def main(data_file, output_file):
    # Load the CSV file into a DataFrame. 
    # I have plenty of memory so let pandas know that to avoid type errors on dose 6 which happens later in the fil

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
    for col in ['Date_COVID_death', 'DateOfPositiveTest', 'DateOfDeath', 'Date_FirstDose', 'Date_ThirdDose']:
        data[col] = pd.to_datetime(data[col] + '-1', format='%G-%V-%u', errors='coerce').dt.date
    # the dt.date will remove the time part of the date so things are cleaner. The  ISO format adds the time.
    # %G-%V-%u because the Czech data uses ISO 8601 weeks
    # format='%Y-%W-%w' was incorrect

    # Create 'died_in_NCmonth' column for deaths between May 30, 2021, and Oct 12, 2021 (inclusive)
    # data['died_in_NCmonth_2021'] = data['DateOfDeath'].apply(lambda x: 1 if pd.notna(x) and pd.Timestamp('2021-05-30') <= x <= pd.Timestamp('2021-10-12') else 0)
    # data['died_in_NCmonth_2022'] = data['DateOfDeath'].apply(lambda x: 1 if pd.notna(x) and pd.Timestamp('2022-05-10') <= x <= pd.Timestamp('2022-07-10') else 0)
    
    #  Drop rows without a first dose. We need to count everyone who got a dose, dead or alive. We gave unvaxxed people a "PLACEBO" does in Jan 2022.
    # data = data.dropna(subset=['Date_FirstDose'])

    # 
    # groupby only summarizes fields with values so ensure that the Code fields have a value "NONE"
    # add date of positive test so can look at mortality of those without a positive test!
    # only fill fields in the index, not in value

    # maybe_empty_fields=['VaccineCode_FirstDose', 'DateOfPositiveTest']
    # data[maybe_empty_fields] = data[maybe_empty_fields].fillna('NONE')    

    # Perform group_by with aggregation. This does all the heavy lifting!
    # summary_df = data.groupby(index_fields).size().reset_index(name="Count")


 

    # generate the three dervied fields
    # (data['A'] > df['B']).astype(int)
    # ata['Date_ThirdDose'].apply(lambda x: 0 if pd.notna(x) and x >= w.start else 1) # 1 is alive at start of wave

    # index fields
    # data[boosted] = (data['Date_ThirdDose'] < data['DateOfPositiveTest']).astype(int)   # boosted before infected
    # data[vaxxed] = (data['Date_FirstDose'] < data['DateOfPositiveTest']).astype(int)  # vaxxed before infected

    # these are the value fields we will sum
    data[COVID_died] = pd.notna(data['Date_COVID_death']).astype(int)   # died from COVID infection 
    # data[infected] = pd.notna(data['DateOfPositiveTest']).astype(int)   # got COVID infection 

    date_vaxxed='Date_FirstDose'
    # create fields so can see stats for infected and DIED after vaccination
    # caution: vaccinated are healthier so this can be misleading unless you are comparing vaxed with vaxxed
    # longitudinally
    
    """
    data[infected_and_vaxxed] = (
        data[date_vaxxed].notna() & 
        data['DateOfPositiveTest'].notna() & 
        (data[date_vaxxed] <= data['DateOfPositiveTest'])
        ).astype(int)

    data[COVID_died_and_vaxxed] = (
        data[date_vaxxed].notna() & 
        data['Date_COVID_death'].notna() & 
        (data[date_vaxxed] <= data['Date_COVID_death'])
        ).astype(int)
    
    # now do for the unvaxxed which is the complement
    data[infected_and_unvaxxed]   = data[infected]-data[infected_and_vaxxed]
    data[COVID_died_and_unvaxxed] = data[COVID_died]-data[COVID_died_and_vaxxed]
    
    """

    # this line does all the work 
    # setting dropna=false allows index entries to include blank (e.g, no vaccinated data) since otherwise those rows are dropped
    # use sum() for adding numeric value fields
    # this is when we were counting date value_fields= ['Date_COVID_death', 'DateOfDeath']    
    # summary_df = data.groupby(index_fields)[value_fields].count().reset_index() 
    # make sure both have dropna=False!!

    # summary_df = data.groupby(index_fields, dropna=False)[value_fields].sum().reset_index()  
    # summary_df["Count"] = data.groupby(index_fields, dropna=False).size().values # add count
    
    # no value fields so can make it a one-liner
    summary_df = data.groupby(index_fields, dropna=False).size().reset_index(name="Count")  
 
    
    # now modify the labels to be more user friendly. Will replace blank with blank
    from mfg_codes import MFG_DICT

    # Transform VaccineCode_xxxDose using the dictionary so have friendly names.
    doses=['d1']
    dose_dict={'d1':'FirstDose','d2':'SecondDose', 'd3':'ThirdDose'}
    
    for d in doses:
        summary_df['VaccineCode_'+dose_dict[d]] = summary_df['VaccineCode_'+dose_dict[d]].map(MFG_DICT) 

    # Now switch back NONE to empty since we used NONE as a placeholder everywhere
    # no need for this anymore since not using NONE
    # summary_df.replace('NONE', '', inplace=True)

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