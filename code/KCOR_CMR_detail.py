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
enrollment_dates = ["2021-06-14", "2022-02-07"]


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
    # Add dose date columns if not already present
    if 'Datum_Druha_davka' not in a_copy.columns:
        a_copy['Datum_Druha_davka'] = pd.NaT
    if 'Datum_Treti_davka' not in a_copy.columns:
        a_copy['Datum_Treti_davka'] = pd.NaT
    if 'Datum_Ctvrta_davka' not in a_copy.columns:
        a_copy['Datum_Ctvrta_davka'] = pd.NaT
    # Convert to datetime
    for col in ['first_dose_date', 'Datum_Druha_davka', 'Datum_Treti_davka', 'Datum_Ctvrta_davka']:
        a_copy[col] = pd.to_datetime(a_copy[col], format='%Y-%m-%d', errors='coerce')
    # Assign dose group as of enrollment date
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
    # Assign birth cohort
    a_copy['born'] = a_copy['birth_year'].apply(lambda x: str(int(x)) if pd.notnull(x) else "unknown")
    # Add week column if not present
    if 'week' not in a_copy.columns:
        a_copy['week'] = a_copy['death_date_lpz'].dt.strftime('%G-%V').astype(str)
    # Restrict to deaths only
    deads_df = a_copy[a_copy['death_date_lpz'].notnull()].copy()
    deads_df['date'] = deads_df['death_date_lpz']
    # Compute weekly death counts for each dose group
    weeks = sorted(a_copy['week'].unique())
    cohorts = sorted(a_copy['born'].unique())
    dose_groups = [0, 1, 2, 3, 4]
    full_index = pd.MultiIndex.from_product([weeks, cohorts, dose_groups], names=['week', 'born', 'dose_group'])
    deads = deads_df.groupby(['week', 'born', 'dose_group']).size().reset_index(name='deaths')
    deads_pivot = deads.pivot_table(index=['week', 'born'], columns='dose_group', values='deaths', fill_value=0)
    print(f"[DEBUG] deads_pivot columns before int cast: {list(deads_pivot.columns)}")
    # Ensure columns are integers and all dose groups 0-4 are present
    deads_pivot.columns = [int(c) for c in deads_pivot.columns]
    print(f"[DEBUG] deads_pivot columns after int cast: {list(deads_pivot.columns)}")
    for d in dose_groups:
        if d not in deads_pivot.columns:
            deads_pivot[d] = 0
    deads_pivot = deads_pivot[dose_groups] if len(deads_pivot) > 0 else pd.DataFrame(columns=dose_groups)
    print(f"[DEBUG] deads_pivot columns after fill: {list(deads_pivot.columns)}")
    print(f"[DEBUG] deads_pivot head:\n{deads_pivot.head()}")
    deads_pivot = deads_pivot.reset_index()
    # Reindex to ensure all week/born combinations exist
    deads_pivot = deads_pivot.set_index(['week', 'born']).reindex(
        pd.MultiIndex.from_product([weeks, cohorts], names=['week', 'born']), fill_value=0
    ).reset_index()

    # Population base as of enrollment date
    a_cohort = a_copy[(a_copy['death_date_lpz'].isna()) | (a_copy['death_date_lpz'] > enrollment_date)]
    pop_base = a_cohort.groupby(['born', 'dose_group']).size().reset_index(name='pop')
    pop_pivot = pop_base.pivot_table(index=['born'], columns='dose_group', values='pop', fill_value=0)
    print(f"[DEBUG] pop_pivot columns before int cast: {list(pop_pivot.columns)}")
    # Ensure columns are integers and all dose groups 0-4 are present
    pop_pivot.columns = [int(c) for c in pop_pivot.columns]
    print(f"[DEBUG] pop_pivot columns after int cast: {list(pop_pivot.columns)}")
    for d in dose_groups:
        if d not in pop_pivot.columns:
            pop_pivot[d] = 0
    pop_pivot = pop_pivot[dose_groups] if len(pop_pivot) > 0 else pd.DataFrame(columns=dose_groups)
    print(f"[DEBUG] pop_pivot columns after fill: {list(pop_pivot.columns)}")
    print(f"[DEBUG] pop_pivot head:\n{pop_pivot.head()}")
    pop_pivot = pop_pivot.reset_index()

    # Merge deaths and population base
    merged = pd.merge(deads_pivot, pop_pivot, on='born', how='left', suffixes=('_dead', '_pop'))
    print(f"[DEBUG] merged columns before CMR: {list(merged.columns)}")
    print(f"[DEBUG] merged head:\n{merged.head()}")
    # For each dose group, compute cumulative deaths, alive at start, CMR
    for dose in dose_groups:
        dead_col = f'{dose}_dead'
        pop_col = f'{dose}_pop'
        merged[f'cum_dead_{dose}'] = merged.groupby('born')[dead_col].cumsum()
        merged[f'alive_start_{dose}'] = merged[f'{pop_col}'] - merged[f'cum_dead_{dose}']
        merged[f'cmr_{dose}'] = merged[dead_col] / merged[f'alive_start_{dose}'] * 365 / 7 * 1e5
    # Save to CSV for this enrollment date
    out_cols = (
        ['week', 'born']
        + [f'cmr_{d}' for d in dose_groups]
        + [f'alive_start_{d}' for d in dose_groups]
        + [f'{d}_dead' for d in dose_groups]
        + [f'{d}_pop' for d in dose_groups]
    )
    merged_out = merged[out_cols].copy()
    merged_out = merged_out[merged_out['week'].notna()]
    # Convert to int for Excel compatibility (only for appropriate columns)
    for col in [f'cmr_{d}' for d in dose_groups] + [f'alive_start_{d}' for d in dose_groups] + [f'{d}_dead' for d in dose_groups] + [f'{d}_pop' for d in dose_groups]:
        merged_out[col] = merged_out[col].replace([np.inf, -np.inf], np.nan).fillna(0).astype(int)
    out_path = f"analysis/fixed_cohort_cmr_{enroll_date_str}.csv"
    # Write to Excel sheet
    sheet_name = enroll_date_str.replace('-', '_')
    merged_out.to_excel(excel_writer, sheet_name=sheet_name, index=False)
    print(f"Added sheet {sheet_name} to {excel_out_path}")

# Save the Excel file after all sheets are added
excel_writer.close()
print(f"Wrote all dose group CMRs to {excel_out_path}")
