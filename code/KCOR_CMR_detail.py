# 
# KCOR_CMR_detail.py
#
# This is a complement to KCOR.py. It generates output to allow computation 
# of CMR (Crude Mortality Rate) for dose 0, 1, 2, 3, and 4 by outputting alive and dead counts by week, birth cohort, and vaccination status.
#
# You can now compute the instantaneous CMR for each dose group by week, birth cohort, and vaccination status.
# 
# You can also compute the HR (Hazard Ratio) for each dose group by week, birth cohort, and vaccination status
# by dividing the CMR of the vaccinated group by the CMR of the unvaccinated group.
# More importantly, can compute the HR for dose 2 vs. dose 1, dose 3 vs. dose 2, and dose 4 vs. dose 3, etc.
# 
# Comparing HRs between dose groups (dose 1 or more) can provide insights into the relative mortality risk associated with each vaccination dose.
# and it eliminates any HVE bias since it doesn't compare vaccinated to unvaccinated.
#
# # This script is designed to analyze mortality trends in relation to vaccination status and there is a list of
# enrollment dates for dose groups.
# 
# It is not a replacement for KCOR.py, but rather an additional analysis script containing population and death data.
# enabling the the analysis of mortality trends in relation to vaccination status.
# It uses the same data format as KCOR.py.
# it does not require the KCOR.py script to run, but it uses the same data format.
# It only looks at first dose vaccination data and ACM death dates.
#
# To run this script, you need to have the data in the same format as KCOR.py. I run it from VS Code (execute the buffer).

# Output file:
#   Czech/analysis/fixed_cohort_cmr.csv
# This is then imported into this spreadsheet for analysis.
#   Czech/analysis/fixed_cohort_cmr.xlsx
#
# This script processes vaccination and death data to compute CMR (Crude Mortality Rate)   
# It loads a dataset, processes it to extract relevant information, computes weekly death counts for vaccinated and unvaccinated individuals, and calculates CMR per 100,000 population per year.
# Computes ages for birth year between 1900 and 2000
# 
# It also shows deaths by birth cohort and vaccination status over time, allowing for analysis of mortality trends in relation to vaccination status.
#     

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Define enrollment dates for dose groups
# These dates are used to determine the dose group for each individual based on their vaccination dates.
enrollment_dates = ["2021-06-14", "2022-02-07", "2023-02-06"]
file_name = "data/vax_24.csv" # The input file name containing vaccination and death data

## Load the dataset with explicit types and rename columns to English
a = pd.read_csv(
    file_name,
    dtype=str,  # Force all columns to string to preserve ISO week format
    low_memory=False
)
a = a.rename(columns={
    'Datum_Prvni_davka': 'first_dose_date',
    'DatumUmrtiLPZ': 'death_date_lpz',  # all cause death date
    # 'DatumUmrti': 'death_date',  # other death date, not used
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
## Remove birth year filtering so all birthdates, including blanks, are included

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


# --------- NEW: Dose group analysis for multiple enrollment dates ---------

### YOU CAN RESTART HERE if code bombs out. This saves time.


excel_out_path = "analysis/fixed_cohort_cmr_dosegroups.xlsx"
excel_writer = pd.ExcelWriter(excel_out_path, engine='xlsxwriter')

# Dose date columns
dose_date_cols = [
    (0, None),
    (1, 'first_dose_date'),
    (2, 'Datum_Druha_davka'),
    (3, 'Datum_Treti_davka'),
    (4, 'Datum_Ctvrta_davka'),
]

for enroll_date_str in enrollment_dates:
    enrollment_date = pd.to_datetime(enroll_date_str)
    a_copy = a.copy()
    # Exclude individuals who died before the enrollment date
    a_copy = a_copy[(a_copy['death_date_lpz'].isna()) | (a_copy['death_date_lpz'] >= enrollment_date)]
    # Add dose date columns if not already present
    for col in ['Datum_Druha_davka', 'Datum_Treti_davka', 'Datum_Ctvrta_davka']:
        if col not in a_copy.columns:
            a_copy[col] = pd.NaT
    import re
    def parse_dose_date(val):
        if pd.isna(val) or val == '':
            return pd.NaT
        # Handle pandas Timestamp or numpy datetime64 directly
        if isinstance(val, (pd.Timestamp, np.datetime64)):
            return pd.to_datetime(val)
        s = str(val)
        # YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            return pd.to_datetime(s, format='%Y-%m-%d', errors='coerce')
        # YYYY-WW
        if re.match(r'^\d{4}-\d{2}$', s):
            # ISO week: YYYY-WW-1 (Monday)
            return pd.to_datetime(s + '-1', format='%G-%V-%u', errors='coerce')
        return pd.NaT
    for col in ['first_dose_date', 'Datum_Druha_davka', 'Datum_Treti_davka', 'Datum_Ctvrta_davka']:
        a_copy[col] = a_copy[col].apply(parse_dose_date)
    # Assign dose group as of enrollment date (highest dose <= enrollment date)
    def get_dose_group(row):
        if pd.notna(row['Datum_Ctvrta_davka']) and row['Datum_Ctvrta_davka'] <= enrollment_date:
            return 4
        elif pd.notna(row['Datum_Treti_davka']) and row['Datum_Treti_davka'] <= enrollment_date:
            return 3
        elif pd.notna(row['Datum_Druha_davka']) and row['Datum_Druha_davka'] <= enrollment_date:
            return 2
        elif pd.notna(row['first_dose_date']) and row['first_dose_date'] <= enrollment_date:
            return 1
        else:
            return 0
    a_copy['dose_group'] = a_copy.apply(get_dose_group, axis=1)
    # Debug: print first record's dose dates and assigned group
    first_row = a_copy.iloc[0]
    print(f"\nFirst record debug for enrollment date {enroll_date_str}:")
    print(f"  Original first_dose_date: {a.iloc[0]['first_dose_date']}")
    print(f"  Parsed first_dose_date: {first_row['first_dose_date']}")
    print(f"  Enrollment date: {enrollment_date}")
    print(f"  Assigned dose group: {first_row['dose_group']}")
    # Make 'born' an integer, using -1 for blanks/NaN
    a_copy['born'] = a_copy['birth_year'].apply(lambda x: int(x) if pd.notnull(x) else -1)

    # Print starting alive counts for each (born, dose_group) in the entire database (ignore death dates)
    print(f"\nStarting alive counts for enrollment date {enroll_date_str} (born, dose_group):")
    alive_counts = a_copy.groupby(['born', 'dose_group']).size().reset_index(name='alive')
    print(alive_counts)
    print(f"Total alive for enrollment date {enroll_date_str}: {alive_counts['alive'].sum()}")
    # Print breakdown by dose group
    dose_group_counts = a_copy.groupby('dose_group').size()
    print(f"Dose group breakdown for enrollment date {enroll_date_str}:")
    for d in [0, 1, 2, 3, 4]:
        print(f"  Dose {d}: {dose_group_counts.get(d, 0)}")
    dose_groups = [0, 1, 2, 3, 4]
    # Compute population base: count of people in each (born, dose_group)
    pop_base = a_copy.groupby(['born', 'dose_group']).size().reset_index(name='pop')
    # Compute deaths per (week, born, dose_group)
    deaths = a_copy[a_copy['death_date_lpz'].notnull()].groupby(['week', 'born', 'dose_group']).size().reset_index(name='dead')
    # Get all weeks in the study period (from min to max week in the data, not just those with deaths)
    # Use all first and last death dates, plus all dose dates, to get the full week range
    all_dates = pd.concat([
        a_copy['first_dose_date'],
        a_copy['Datum_Druha_davka'],
        a_copy['Datum_Treti_davka'],
        a_copy['Datum_Ctvrta_davka'],
        a_copy['death_date_lpz']
    ]).dropna()
    min_week = all_dates.min().isocalendar().week
    min_year = all_dates.min().isocalendar().year
    max_week = all_dates.max().isocalendar().week
    max_year = all_dates.max().isocalendar().year
    # Build all weeks between min and max
    from datetime import date, timedelta
    def week_year_iter(y1, w1, y2, w2):
        d = date.fromisocalendar(y1, w1, 1)
        dend = date.fromisocalendar(y2, w2, 1)
        while d <= dend:
            yield d.isocalendar()[:2]
            # next week
            d += timedelta(days=7)
    all_weeks = [f"{y}-{str(w).zfill(2)}" for y, w in week_year_iter(min_year, min_week, max_year, max_week)]
    cohorts = sorted(a_copy['born'].dropna().unique())
    # Build MultiIndex for all (week, born)
    index = pd.MultiIndex.from_product([all_weeks, cohorts], names=['week', 'born'])
    # Prepare output DataFrame
    out = pd.DataFrame(index=index)
    for d in dose_groups:
        # deaths for this group
        deaths_d = deaths[deaths['dose_group'] == d].set_index(['week', 'born'])['dead']
        out[f'{d}_dead'] = deaths_d.reindex(index, fill_value=0).values
        # pop for this group (initial for all weeks)
        pop_d = pop_base[pop_base['dose_group'] == d].set_index('born')['pop']
        out[f'{d}_pop'] = [pop_d.get(born, 0) for week, born in out.index]

    out = out.reset_index()
    out['week'] = out['week'].astype(str)
    out['born'] = out['born'].astype('Int64')

    # Overwrite population columns to reflect attrition from deaths (vectorized)
    out = out.sort_values(['born', 'week'])
    for d in dose_groups:
        pop_col = f'{d}_pop'
        dead_col = f'{d}_dead'
        for born, group in out.groupby('born'):
            pop = group[pop_col].values.astype(int)
            dead = group[dead_col].values.astype(int)
            alive = np.empty_like(pop)
            alive[0] = pop[0]
            for i in range(1, len(pop)):
                alive[i] = max(alive[i-1] - dead[i-1], 0)
            out.loc[group.index, pop_col] = alive
    # Write to Excel sheet
    sheet_name = enroll_date_str.replace('-', '_')
    out.to_excel(excel_writer, sheet_name=sheet_name, index=False)
    print(f"Added sheet {sheet_name} to {excel_out_path}")

# Save the Excel file after all sheets are added
excel_writer.close()
print(f"Wrote all dose group CMRs to {excel_out_path}")
