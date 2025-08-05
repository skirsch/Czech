# 
# KCOR_CMR_detail.py
#
# This is a complement to KCOR.py. It generates output to allow computation of CMR (Crude Mortality Rate) for vaccinated and unvaccinated individuals.
# it does not require the KCOR.py script to run, but it uses the same data format.
# It only looks at first dose vaccination data and ACM death dates.
#
# This script processes vaccination and death data to compute CMR (Crude Mortality Rate)   
# It loads a dataset, processes it to extract relevant information, computes weekly death counts for vaccinated and unvaccinated individuals, and calculates CMR per 100,000 population per year.
# Computes ages for birth year between 1900 and 2000
# 
# It also shows deaths by birth cohort and vaccination status over time, allowing for analysis of mortality trends in relation to vaccination status.
#     
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

## Load the dataset with explicit types and rename columns to English
a = pd.read_csv(
    "../czech/data/vax_24.csv",
    dtype={
        'Datum_Prvni_davka': str,
        'DatumUmrtiLPZ': str,
        'RokNarozeni': str
    },
    low_memory=False
)
a = a.rename(columns={
    'Datum_Prvni_davka': 'first_dose_date',
    'DatumUmrtiLPZ': 'death_date_lpz',  # all cause death date
    'DatumUmrti': 'death_date',  # other death date, not used
    'RokNarozeni': 'birth_year_range',
    'Infekce': 'Infection'     # infection count. Need to filter out 2 or more to eliminate duplicate death reports (can't do by ID number) 
})

# if you got infected more than once, it will create a duplicate record (with a different ID) so
# remove those records so we don't double count the deaths.

# Remove records where Infection > 1
a = a[(a['Infection'].fillna(0).astype(int) <= 1)]



# Convert relevant columns to datetime (ISO format assumed: YYYY-MM-DD)
# Extract cohort year from birth year range (e.g., '1970-1974' -> 1970)
a['birth_year'] = a['birth_year_range'].str.extract(r'(\d{4})').astype(float)
# Limit to cohorts born 1900-2020
# This will also convert NaN birth years to NaN, which we can handle later
a = a[(a['birth_year'] >= 1900) & (a['birth_year'] <= 2020)]

# Parse ISO week format for first dose and death date
a['first_dose_date'] = pd.to_datetime(a['first_dose_date'].str.replace(r'[^0-9-]', '', regex=True) + '-1', format='%G-%V-%u', errors='coerce')
a['death_date_lpz'] = pd.to_datetime(a['death_date_lpz'].str.replace(r'[^0-9-]', '', regex=True) + '-1', format='%G-%V-%u', errors='coerce')
a['week'] = a['death_date_lpz'].dt.strftime('%G-%V').astype(str)

# Extract year from birth_year string (first 4 chars)
a['birth_year'] = a['birth_year'].astype(str).str[:4]
a['birth_year'] = pd.to_numeric(a['birth_year'], errors='coerce')

# Fix death dates
## Only use LPZ death date, ignore other death date
a = a[~((a['death_date_lpz'].notnull()) & (a['first_dose_date'] > a['death_date_lpz']))]

# Define fixed vaccination status as of 2021-24
enrollment_date = pd.to_datetime("2021-06-14")  # ISO week 2021-24 starts on 2021-06-14
a['fixed_vax'] = a['first_dose_date'] <= enrollment_date # Matches KCOR.py logic

# Assign birth cohort

print("birth_year head:", a['birth_year'].head())
a['born'] = a['birth_year'].apply(lambda x: str(int(x)) if pd.notnull(x) else "unknown")

# All further processing is done on a copy
# so can re-run from here without reloading

df = a.copy()

# Restrict to deaths only
print("death_date_lpz notnull count:", a['death_date_lpz'].notnull().sum())
print("death_date_lpz head:", a['death_date_lpz'].head(20))
# For deaths, filter to those with a death date
deads_df = a[a['death_date_lpz'].notnull()].copy()
deads_df['date'] = deads_df['death_date_lpz']

# Compute weekly death counts for fixed-vax and fixed-unvax
weeks = sorted(df['week'].unique())
cohorts = sorted(df['born'].unique())
full_index = pd.MultiIndex.from_product([weeks, cohorts], names=['week', 'born'])
deads = deads_df.groupby(['week', 'born', 'fixed_vax']).size().reset_index(name='deaths')
deads_pivot = deads.pivot_table(index=['week', 'born'], columns='fixed_vax', values='deaths', fill_value=0)
deads_pivot = deads_pivot.rename(columns={False: 'unvax_dead', True: 'vax_dead'})
deads_pivot = deads_pivot.reindex(full_index, fill_value=0).reset_index()
print("deads born:", deads_pivot['born'].unique())

# Population base as of 2021-24
## Use a copy of the already loaded and processed data for population base
a_cohort = a.copy()  # Do NOT filter by death_date_lpz
# Only include individuals alive at the enrollment date
a_cohort = a_cohort[(a_cohort['death_date_lpz'].isna()) | (a_cohort['death_date_lpz'] > enrollment_date)]
pop_base = a_cohort.groupby(['born', 'fixed_vax']).size().reset_index(name='pop')
pop_pivot = pop_base.pivot_table(index=['born'], columns='fixed_vax', values='pop', fill_value=0)
pop_pivot = pop_pivot.rename(columns={False: 'unvax_pop', True: 'vax_pop'}).reset_index()
print("pop_base born:", pop_pivot['born'].unique())

# Merge population with death counts

# Merge deaths and population base on all relevant keys using an outer join


# Merge deaths and population base on birth cohort and week
merged = pd.merge(
    deads_pivot,
    pop_pivot,
    on=['born'],
    how='left'
)

# Forward fill population columns for each cohort so every week has the correct population
for col in ['vax_pop', 'unvax_pop']:
    merged[col] = merged.groupby('born')[col].ffill().bfill()

# Only compute CMR for weeks after the enrollment date
enrollment_week = pd.to_datetime('2021-06-14').strftime('%G-%V')
merged = merged[merged['week'] >= enrollment_week]

# Sort by cohort and week for cumulative calculation
merged = merged.sort_values(['born', 'week'])

# Compute cumulative deaths for each cohort and vaccination status up to each week
merged['cum_vax_dead'] = merged.groupby(['born'])['vax_dead'].cumsum()
merged['cum_unvax_dead'] = merged.groupby(['born'])['unvax_dead'].cumsum()

# Number alive at start of week (before deaths in that week)
merged['vax_alive_start'] = merged['vax_pop'] - merged['cum_vax_dead']
merged['unvax_alive_start'] = merged['unvax_pop'] - merged['cum_unvax_dead']

# Number dead in that week (already present)
merged['vax_dead_week'] = merged['vax_dead']
merged['unvax_dead_week'] = merged['unvax_dead']

# Number alive at end of week (after deaths in that week)
merged['vax_alive_end'] = merged['vax_alive_start'] + merged['vax_dead_week']
merged['unvax_alive_end'] = merged['unvax_alive_start'] + merged['unvax_dead_week']

# For CMR calculation, use alive at start of week
merged['vax_alive'] = merged['vax_alive_start']
merged['unvax_alive'] = merged['unvax_alive_start']

# Compute CMR per 100,000 per year (weekly deaths scaled) using alive population
merged['vax_cmr'] = merged['vax_dead'] / merged['vax_alive'] * 365 / 7 * 1e5
merged['unvax_cmr'] = merged['unvax_dead'] / merged['unvax_alive'] * 365 / 7 * 1e5

# Save to CSV or return dataframe as needed

# Compute all-ages summary for each week

# Compute initial population for all ages

# Get initial population for all ages (first week per cohort)
first_week_mask = merged.groupby('born')['week'].transform('min') == merged['week']
initial_vax_pop = merged.loc[first_week_mask, 'vax_pop'].sum()
initial_unvax_pop = merged.loc[first_week_mask, 'unvax_pop'].sum()

# Compute cumulative deaths for all ages per week
all_ages_deaths = merged.groupby('week').agg({
    'vax_dead_week': 'sum',
    'unvax_dead_week': 'sum'
}).reset_index()
all_ages_deaths['cum_vax_dead'] = all_ages_deaths['vax_dead_week'].cumsum()
all_ages_deaths['cum_unvax_dead'] = all_ages_deaths['unvax_dead_week'].cumsum()

# Alive at start of week = initial population - cumulative deaths
all_ages_deaths['vax_alive_start'] = initial_vax_pop - all_ages_deaths['cum_vax_dead']
all_ages_deaths['unvax_alive_start'] = initial_unvax_pop - all_ages_deaths['cum_unvax_dead']

all_ages_deaths['born'] = 'all_ages'
all_ages_deaths['vax_cmr'] = all_ages_deaths['vax_dead_week'] / all_ages_deaths['vax_alive_start'] * 365 / 7 * 1e5
all_ages_deaths['unvax_cmr'] = all_ages_deaths['unvax_dead_week'] / all_ages_deaths['unvax_alive_start'] * 365 / 7 * 1e5

# Reorder columns to match merged
all_ages = all_ages_deaths[['week', 'born', 'vax_cmr', 'unvax_cmr', 'vax_alive_start', 'unvax_alive_start', 'vax_dead_week', 'unvax_dead_week']]
# Remove rows with NaN week from both merged and all_ages before concatenation
merged_clean = merged[['week', 'born', 'vax_cmr', 'unvax_cmr', 'vax_alive_start', 'unvax_alive_start', 'vax_dead_week', 'unvax_dead_week']].copy()
merged_clean = merged_clean[merged_clean['week'].notna()]
all_ages = all_ages[all_ages['week'].notna()]

# Append all-ages rows to merged
merged_out = pd.concat([merged_clean, all_ages], ignore_index=True)

# Remove rows with NaN week
merged_out = merged_out[merged_out['week'].notna()]

# Convert CMR columns to integer type for Excel compatibility
for col in ['vax_cmr', 'unvax_cmr', 'vax_alive_start', 'unvax_alive_start', 'vax_dead_week', 'unvax_dead_week']:
    merged_out[col] = merged_out[col].fillna(0).astype(int)

merged_out.to_csv("analysis/fixed_cohort_cmr.csv", index=False)
print(merged_out.head())
