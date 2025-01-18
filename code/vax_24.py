# new vax record level data released in Nov 2024
# Hence the filename vax_24.py for the analysis of the 2024 Czech Republic data

# Data file: https://www.nzip.cz/data/2135-covid-19-prehled-populace
#
# written about here: https://smis-lab.cz/2024/11/07/dalsi-velka-datova-sada-uzis-zverejnena/


# all fields (in English)
# ID,Infection,Gender,YearOfBirth,DateOfPositiveTest,DateOfResult,Recovered,Deceased,Symptom,TestType,Date_FirstDose,Date_SecondDose,Date_ThirdDose,Date_FourthDose,Date_FifthDose,Date_SixthDose,Date_SeventhDose,
# VaccineCode_FirstDose,VaccineCode_SecondDose,VaccineCode_ThirdDose,VaccineCode_FourthDose,VaccineCode_FifthDose,VaccineCode_SixthDose,VaccineCode_SeventhDose,PrimaryCauseHospCOVID,bin_Hospitalization,min_Hospitalization,days_Hospitalization,max_Hospitalization,bin_ICU,min_ICU,days_ICU,max_ICU,bin_StandardWard,min_StandardWard,days_StandardWard,max_StandardWard,bin_Oxygen,min_Oxygen,days_Oxygen,max_Oxygen,bin_HFNO,min_HFNO,days_HFNO,max_HFNO,bin_MechanicalVentilation_ECMO,min_MechanicalVentilation_ECMO,
# days_MechanicalVentilation_ECMO,max_MechanicalVentilation_ECMO,Mutation,DateOfDeath,Long_COVID,DCCI

# index: YearOfBirth, VaccineCode_FirstDose, Date_FirstDose, Infection, DCCI, 
# value: # records, died in 30, 60, 90, 120, 150, 180, etc. of shot till 360 using the DateOfDeathLPZ

# data.dtypes() to print out datatypes
import pandas as pd

data_file='../data/CR=24.csv'
data_file='../data/sample.csv'
output_file = '../data/CR-24_summary.csv'

# Load the CSV file into a DataFrame. I already replaced the headers as above.
data = pd.read_csv(data_file)

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
value_fields = ['Countd1', 'Died_90d1', 'Died_180d1', 'Died_270d1', 'Died_360d1', 
                'Countd2', 'Died_90d2', 'Died_180d2', 'Died_270d2', 'Died_360d2', 
                'Countd3', 'Died_90d3', 'Died_180d3', 'Died_270d3', 'Died_360d3']

# Transform YearOfBirth to extract the first year as an integer, handling missing or invalid entries
data['YearOfBirth'] = data['YearOfBirth'].str.split('-').str[0].replace('', None).dropna().astype('Int32')

# Transform the VaccineCode columns to clean then up
# now need to upper case everything and remove leading and trailing spaces
brand_cols=['VaccineCode_FirstDose', 'VaccineCode_SecondDose', 'VaccineCode_ThirdDose']
for col in brand_cols:
    data[col] = data[col].str.strip().str.upper()

# Ensure Infection is an integer (empty=0)
data['Infection'] = data['Infection'].fillna(0).astype('Int32')

# Convert dates from YYYY-WW format to pandas datetime format
for col in ['Date_FirstDose', 'Date_SecondDose','Date_ThirdDose', 'DateOfDeath']:
    data[col] = pd.to_datetime(data[col] + '-1', format='%Y-%W-%w', errors='coerce')

# only Drop rows without a first dose. We need to count everyone who got a dose, dead or alive
data = data.dropna(subset=['Date_FirstDose'])

doses=['d1', 'd2','d3']
dose_dict={'d1':'FirstDose','d2':'SecondDose', 'd3':'ThirdDose'}
day_list=[90,180,270,360]

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

# Perform group_by with aggregation
summary_df = data.groupby(index_fields)[value_fields].sum().reset_index()

# now modify the labels to be more user friendly
from mfg_codes import MFG_DICT

# Transform VaccineCode_xxxDose using the dictionary
for d in doses:
    summary_df['VaccineCode_'+dose_dict[d]] = summary_df['VaccineCode_'+dose_dict[d]].map(MFG_DICT).fillna(data['VaccineCode_'+dose_dict[d]])
# summary_df['VaccineCode_FirstDose'] = summary_df['VaccineCode_FirstDose'].map(MFG_DICT).fillna(data['VaccineCode_FirstDose'])


# Write the summary DataFrame to a CSV file
summary_df.to_csv(output_file, index=False)

print(f"Summary file has been written to {output_file}.")
