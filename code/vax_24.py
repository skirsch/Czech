# new vax record level data released in Nov 2024
# https://www.nzip.cz/data/2135-covid-19-prehled-populace
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

# Load the CSV file into a DataFrame
data = pd.read_csv('../data/sample.csv')

# Define the index and value fields
index_fields = ['YearOfBirth', 'VaccineCode_FirstDose', 'Date_FirstDose', 'Infection', 'DCCI']
value_fields = ['Count', 'Died_90d', 'Died_180d', 'Died_270d', 'Died_360d']

# Transform YearOfBirth to extract the first year as an integer, handling missing or invalid entries
data['YearOfBirth'] = data['YearOfBirth'].str.split('-').str[0].replace('', None).dropna().astype('Int32')

# Ensure Infection is an integer
data['Infection'] = data['Infection'].fillna(0).astype('Int32')

# Convert dates from YYYY-WW format to pandas datetime format
data['Date_FirstDose'] = pd.to_datetime(data['Date_FirstDose'] + '-1', format='%Y-%W-%w', errors='coerce')
data['DateOfDeath'] = pd.to_datetime(data['DateOfDeath'] + '-1', format='%Y-%W-%w', errors='coerce')

# only Drop rows without a dose. We need to count everyone, dead or aliev
data = data.dropna(subset=['Date_FirstDose'])

# Compute days till death (dtd) and convert to int32
data['dtd'] = (data['DateOfDeath'] - data['Date_FirstDose']).dt.days.astype('Int32')

# Compute the Count and Died_xxd fields using the dtd column
data['Count'] = 1
data['Died_90d'] = data['dtd'].apply(lambda x: 1 if pd.notna(x) and x <= 90 else 0)
data['Died_180d'] = data['dtd'].apply(lambda x: 1 if pd.notna(x) and x <= 180 else 0)
data['Died_270d'] = data['dtd'].apply(lambda x: 1 if pd.notna(x) and x <= 270 else 0)
data['Died_360d'] = data['dtd'].apply(lambda x: 1 if pd.notna(x) and x <= 360 else 0)

# Perform group_by with aggregation
summary_df = data.groupby(index_fields)[value_fields].sum().reset_index()

# now modify the labels to be more user friendly
from mfg_codes import MFG_DICT

# Transform VaccineCode_FirstDose using the dictionary
summary_df['VaccineCode_FirstDose'] = summary_df['VaccineCode_FirstDose'].map(MFG_DICT).fillna(data['VaccineCode_FirstDose'])


# Write the summary DataFrame to a CSV file
output_file = '../data/summary_output.csv'
summary_df.to_csv(output_file, index=False)

print(f"Summary file has been written to {output_file}.")
