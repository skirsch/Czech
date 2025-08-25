
import pandas as pd
import numpy as np

# Load and process the same way as KCOR_CMR.py
a = pd.read_csv('data/vax_24.csv', dtype=str, low_memory=False)
a = a.rename(columns={
    'Datum_Prvni_davka': 'first_dose_date',
    'DatumUmrtiLPZ': 'death_date_lpz',
    'RokNarozeni': 'birth_year_range',
    'Infekce': 'Infection'
})

# Remove duplicates
a = a[(a['Infection'].fillna(0).astype(int) <= 1)]

# Parse birth year
a['birth_year'] = a['birth_year_range'].str.extract(r'(\d{4})').astype(float)
a['birth_year'] = a['birth_year'].astype(str).str[:4]
a['birth_year'] = pd.to_numeric(a['birth_year'], errors='coerce')
a['born'] = a['birth_year'].apply(lambda x: int(x) if pd.notnull(x) else -1)

# Parse death dates
a['death_date_lpz'] = pd.to_datetime(a['death_date_lpz'].str.replace(r'[^0-9-]', '', regex=True) + '-1', format='%G-%V-%u', errors='coerce')
a['week'] = a['death_date_lpz'].dt.strftime('%G-%V').astype(str)

print(f'Total records: {len(a)}')
print(f'Records with deaths: {a["death_date_lpz"].notnull().sum()}')

# Check deaths for born 1950
born_1950 = a[a['born'] == 1950]
deaths_1950 = born_1950[born_1950['death_date_lpz'].notnull()]
print(f'Born 1950 total: {len(born_1950)}')
print(f'Born 1950 deaths: {len(deaths_1950)}')

# Count deaths by week for born 1950
if len(deaths_1950) > 0:
    weekly_deaths = deaths_1950.groupby('week').size()
    print(f'Max weekly deaths for born 1950: {weekly_deaths.max()}')
    print(f'Top 5 weeks with most deaths:')
    print(weekly_deaths.nlargest(5))