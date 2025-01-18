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
data = pd.read_csv('sample.csv')

# Define the index and value fields
index_fields = ['YearOfBirth', 'VaccineCode_FirstDose', 'Date_FirstDose', 'Infection', 'DCCI']
value_fields = ['Count', 'Died_90d', 'Died_180d', 'Died_270d', 'Died_360d']

# Transform YearOfBirth to extract the first year as an integer, handling missing or invalid entries
data['YearOfBirth'] = data['YearOfBirth'].str.split('-').str[0].replace('', None).dropna().astype(int)

# Ensure Infection is an integer
data['Infection'] = data['Infection'].fillna(0).astype(int)

# Convert dates from YYYY-WW format to pandas datetime format
data['Date_FirstDose'] = pd.to_datetime(data['Date_FirstDose'] + '-1', format='%Y-%W-%w', errors='coerce')
data['DateOfDeath'] = pd.to_datetime(data['DateOfDeath'] + '-1', format='%Y-%W-%w', errors='coerce')

# Drop rows with invalid or missing dates
data = data.dropna(subset=['Date_FirstDose', 'DateOfDeath'])

# Compute the Count and Died_xxd fields
data['Count'] = 1

data['Died_90d'] = ((data['DateOfDeath'] - data['Date_FirstDose']).dt.days <= 90).astype(int)
data['Died_180d'] = ((data['DateOfDeath'] - data['Date_FirstDose']).dt.days <= 180).astype(int)
data['Died_270d'] = ((data['DateOfDeath'] - data['Date_FirstDose']).dt.days <= 270).astype(int)
data['Died_360d'] = ((data['DateOfDeath'] - data['Date_FirstDose']).dt.days <= 360).astype(int)

# Perform group_by with aggregation
summary_df = data.groupby(index_fields)[value_fields].sum().reset_index()

# Write the summary DataFrame to a CSV file
output_file = 'summary_output.csv'
summary_df.to_csv(output_file, index=False)

print(f"Summary file has been written to {output_file}.")
