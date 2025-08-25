import pandas as pd
import numpy as np

# Load raw data
print("Loading raw data...")
a = pd.read_csv('data/vax_24.csv', dtype=str, low_memory=False)
print(f'Raw records: {len(a)}')

# Check for duplicates BEFORE any filtering
print(f'Unique records by all columns: {a.nunique().min()}')
print(f'Duplicate rows (exact): {a.duplicated().sum()}')

# Check the Infection column
print(f'\nInfection column values:')
print(a['Infekce'].value_counts(dropna=False).head(10))

# Apply infection filter
print(f'\nApplying infection filter...')
a_filtered = a[(a['Infekce'].fillna(0).astype(int) <= 1)]
print(f'After infection filter: {len(a_filtered)} (removed {len(a) - len(a_filtered)})')

# Rename columns
a_filtered = a_filtered.rename(columns={
    'Datum_Prvni_davka': 'first_dose_date',
    'DatumUmrtiLPZ': 'death_date_lpz',
    'RokNarozeni': 'birth_year_range',
    'Infekce': 'Infection'
})

# Parse birth year
a_filtered['birth_year'] = a_filtered['birth_year_range'].str.extract(r'(\d{4})').astype(float)
a_filtered['birth_year'] = a_filtered['birth_year'].astype(str).str[:4]
a_filtered['birth_year'] = pd.to_numeric(a_filtered['birth_year'], errors='coerce')
a_filtered['born'] = a_filtered['birth_year'].apply(lambda x: int(x) if pd.notnull(x) else -1)

print(f'\nBirth year distribution:')
print(a_filtered['born'].value_counts().head(10))

# Parse death dates
a_filtered['death_date_lpz'] = pd.to_datetime(
    a_filtered['death_date_lpz'].str.replace(r'[^0-9-]', '', regex=True) + '-1', 
    format='%G-%V-%u', errors='coerce'
)

print(f'\nDeath date parsing:')
print(f'Total records: {len(a_filtered)}')
print(f'Records with death dates: {a_filtered["death_date_lpz"].notnull().sum()}')

# Focus on born 1950
born_1950 = a_filtered[a_filtered['born'] == 1950]
deaths_1950 = born_1950[born_1950['death_date_lpz'].notnull()]

print(f'\nBorn 1950 analysis:')
print(f'Total born 1950: {len(born_1950)}')
print(f'Deaths born 1950: {len(deaths_1950)}')

# Check for duplicate death records
if len(deaths_1950) > 0:
    print(f'\nDuplicate analysis for born 1950 deaths:')
    # Check if same person appears multiple times
    if 'ID' in deaths_1950.columns:
        unique_ids = deaths_1950['ID'].nunique()
        print(f'Unique IDs in deaths: {unique_ids}')
        print(f'Total death records: {len(deaths_1950)}')
        if unique_ids < len(deaths_1950):
            print(f'PROBLEM: Same person appears multiple times in death records!')
            duplicated_ids = deaths_1950[deaths_1950.duplicated(subset=['ID'], keep=False)]['ID'].unique()
            print(f'Duplicated IDs: {len(duplicated_ids)}')
    
    # Look at the actual death week distribution
    deaths_1950['week'] = deaths_1950['death_date_lpz'].dt.strftime('%G-%V')
    weekly_deaths = deaths_1950.groupby('week').size()
    print(f'\nWeekly death pattern for born 1950:')
    print(f'Max: {weekly_deaths.max()}, Min: {weekly_deaths.min()}, Mean: {weekly_deaths.mean():.1f}')
    print(f'Weeks with >100 deaths: {(weekly_deaths > 100).sum()}')
    print(f'Weeks with >300 deaths: {(weekly_deaths > 300).sum()}')
    
    print(f'\nTop 10 weeks with most deaths:')
    print(weekly_deaths.nlargest(10))
