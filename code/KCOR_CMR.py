# 
#   KCOR_CMR.py
#
# Analysis script for CMR for vaccination dose groups
#
# I run it from VS Code (execute the buffer). It takes about 10 minutes to run for each enrollment date.
# Be sure you have pandas, numpy, matplotlib, and seaborn installed in your python environment.
# You can install them with pip if needed:   
#  pip install pandas numpy matplotlib seaborn (or apt install python3-pandas python3-numpy python3-matplotlib python3-seaborn on WSL)

# You can also run it from the command line but be sure you have seaborn installed in your python environment.
# You can install seaborn with pip if needed:   pip install seaborn (or apt install python3-seaborn on WSL)

#   cd code; make KCOR_CMR

# Output file:
#   Czech/analysis/fixed_cohort_cmr_dosegroups.xlsx
#
# The output file contains the CMR for each dose group by week, birth cohort, and vaccination status.
# The output file contains multiple sheets, one for each enrollment date.
# The output file contains the alive and dead counts by week, birth cohort, and vaccination status.
# The output file columns are:
#   week: ISO week (YYYY-WW)
#   born: birth year (e.g., 1970)
#   0_pop: population alive in dose group 0 (unvaccinated)
#   0_dead: deaths in dose group 0 (unvaccinated)
#   1_pop: population alive in dose group 1 (1 dose)
#   1_dead: deaths in dose group 1 (1 dose)
#   2_pop: population alive in dose group 2 (2 doses)
#   2_dead: deaths in dose group 2 (2 doses)
#   ... and so on for dose groups 3 and 4
#
# The population counts are adjusted for deaths over time (attrition).
#
# The data is then imported into this spreadsheet for analysis.
#   Czech/analysis/fixed_cohort_cmr_dosegroups_analysis.xlsx
#
# This script processes vaccination and death data to compute CMR (Crude Mortality Rate) for each age cohort and vaccination dose group (0, 1, 2, 3, 4). 
# It loads the Czech dataset, processes it to extract relevant information, computes weekly death counts for vaccinated and unvaccinated individuals, and calculates CMR per 100,000 population per year.
# Computes ages for birth year between 1900 and 2000
# 
# It also shows deaths by birth cohort and vaccination status over time, allowing for analysis of mortality trends in relation to vaccination status.
#
# This creates output files that are analyzed in files in analysis/fixed_cohort_CMR.... files.
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


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# US 2000 Standard Population for ASMR calculation (19 age groups)
# Source: https://seer.cancer.gov/stdpopulations/stdpop.19ages.html
US_2000_STANDARD_POP = {
    "<1": 13818,
    "1-4": 55317,
    "5-9": 72533,
    "10-14": 73032,
    "15-19": 72169,
    "20-24": 66478,
    "25-29": 64529,
    "30-34": 71044,
    "35-39": 80762,
    "40-44": 81851,
    "45-49": 72118,
    "50-54": 62716,
    "55-59": 48454,
    "60-64": 38793,
    "65-69": 34264,
    "70-74": 31773,
    "75-79": 26999,
    "80-84": 17842,
    "85+": 15508,
}

AGE_BINS = [
    ("<1",   0,   0),    # age == 0 years (~<1)
    ("1-4",  1,   4),
    ("5-9",  5,   9),
    ("10-14",10, 14),
    ("15-19",15, 19),
    ("20-24",20, 24),
    ("25-29",25, 29),
    ("30-34",30, 34),
    ("35-39",35, 39),
    ("40-44",40, 44),
    ("45-49",45, 49),
    ("50-54",50, 54),
    ("55-59",55, 59),
    ("60-64",60, 64),
    ("65-69",65, 69),
    ("70-74",70, 74),
    ("75-79",75, 79),
    ("80-84",80, 84),
    ("85+",  85, 200),   # cap at 200
]

def age_to_group(age_years: int) -> str:
    """Map integer age to US2000 19-group label."""
    if pd.isna(age_years):
        return None
    age = int(age_years)
    for label, a0, a1 in AGE_BINS:
        if a0 <= age <= a1:
            return label
    return None

def approx_age_from_born(week_date, born_year) -> int:
    """
    Approx age in whole years at week_date when only a birth YEAR is known.
    Uses July 1st as mid-year proxy.
    """
    if pd.isna(born_year) or born_year == -1:
        return None
    from datetime import date
    # Convert week_date to date if it's a pandas Timestamp
    if hasattr(week_date, 'date'):
        week_d = week_date.date()
    else:
        week_d = pd.to_datetime(week_date).date()
    dob_proxy = date(int(born_year), 7, 1)
    return max(0, int((week_d - dob_proxy).days // 365.2425))

# define the output Excel file path
# This will contain the CMR for each dose group by week, birth cohort, and vaccination status.
# This is used to compute the HR (Hazard Ratio) for each dose group by week, birth cohort, and vaccination status
# and it eliminates any HVE bias since it doesn't compare vaccinated to unvaccinated.
excel_out_path = "../analysis/fixed_cohort_cmr_dosegroups.xlsx"
excel_writer = pd.ExcelWriter(excel_out_path, engine='xlsxwriter')


# Define enrollment dates for dose groups
# These dates are used to determine the dose group for each individual based on their vaccination dates.
# These are ISO week format: YYYY-WW
# The enrollment date is the date when the individual is considered to be part of the study cohort.
# 2021-W13 is 03-29-2021, the start of the vaccination campaign
# 2021-W24 is 06-14-2021, when everyone 40+ was eligible for first dose.
# 2021-W41 is 10-11-2021, which is a late enrollment date before the winter wave.
# 2022-W47 is 11-21-2022, which is the best booster #2 enrollment since it is just before everyone got 2nd booster.
# 2024-W01 is 12-30-2023, which is the best booster #3 enrollment since it is just before everyone got 3rd booster.
enrollment_dates = ['2021-13', '2021-24', '2021-41', '2022-06', '2022-47', '2024-01']

file_name = "../data/vax_24.csv" # The input file name containing vaccination and death data

## Load the dataset with explicit types and rename columns to English
print(f"  Reading the input file: {file_name}")


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

# Parse ISO week format for death date only (first_dose_date will be parsed later)
a['death_date_lpz'] = pd.to_datetime(a['death_date_lpz'].str.replace(r'[^0-9-]', '', regex=True) + '-1', format='%G-%V-%u', errors='coerce')
a['week'] = a['death_date_lpz'].dt.strftime('%G-%V').astype(str)

# Extract year from birth_year string (first 4 chars)
a['birth_year'] = a['birth_year'].astype(str).str[:4]
a['birth_year'] = pd.to_numeric(a['birth_year'], errors='coerce')

# --------- Parse all dose dates ONCE before the enrollment loop ---------
print(f"Parsing dose date columns (one time only)...")
# Add dose date columns if not already present
for col in ['Datum_Druha_davka', 'Datum_Treti_davka', 'Datum_Ctvrta_davka']:
    if col not in a.columns:
        a[col] = pd.NaT

# Use the fast vectorized ISO week parsing approach (same as KCOR.py)
dose_date_columns = ['first_dose_date', 'Datum_Druha_davka', 'Datum_Treti_davka', 'Datum_Ctvrta_davka']
for col in dose_date_columns:
    print(f"  Parsing {col}...")
    # Fast vectorized ISO week parsing: YYYY-WW + '-1' -> datetime (keep as Timestamp, not .date)
    a[col] = pd.to_datetime(a[col] + '-1', format='%G-%V-%u', errors='coerce')
print(f"Dose date parsing complete for all columns.")

# Fix death dates - now we can compare properly since all dates are pandas Timestamps
## Only use LPZ death date, ignore other death date
a = a[~((a['death_date_lpz'].notnull()) & (a['first_dose_date'] > a['death_date_lpz']))]

# Convert birth years to integers once (outside the enrollment loop)
print(f"Converting birth years to integers (one time only)...")
a['born'] = a['birth_year'].apply(lambda x: int(x) if pd.notnull(x) else -1)
print(f"Birth year conversion complete.")

# --------- NEW: Dose group analysis for multiple enrollment dates ---------

### YOU CAN RESTART HERE if code bombs out. This saves time.

# Dose date columns
dose_date_cols = [
    (0, None),
    (1, 'first_dose_date'),
    (2, 'Datum_Druha_davka'),
    (3, 'Datum_Treti_davka'),
    (4, 'Datum_Ctvrta_davka'),
]

for enroll_date_str in enrollment_dates:
    # Parse ISO week string as Monday of that week
    import datetime
    print(f"Processing enrollment date {enroll_date_str} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    enrollment_date = pd.to_datetime(enroll_date_str + '-1', format='%G-%V-%u', errors='coerce')
    print(f"  Creating copy of dataset ({len(a)} records)...")
    a_copy = a.copy()
    print(f"  Filtering out deaths before enrollment date...")
    # Exclude individuals who died before the enrollment date
    a_copy = a_copy[(a_copy['death_date_lpz'].isna()) | (a_copy['death_date_lpz'] >= enrollment_date)]
    print(f"  Records after enrollment filter: {len(a_copy)}")
    
    # Assign dose group as of enrollment date (highest dose <= enrollment date) - VECTORIZED VERSION
    print(f"  Assigning dose groups...")
    
    # Create boolean masks for each dose being valid (not null and <= enrollment_date)
    dose1_valid = a_copy['first_dose_date'].notna() & (a_copy['first_dose_date'] <= enrollment_date)
    dose2_valid = a_copy['Datum_Druha_davka'].notna() & (a_copy['Datum_Druha_davka'] <= enrollment_date)
    dose3_valid = a_copy['Datum_Treti_davka'].notna() & (a_copy['Datum_Treti_davka'] <= enrollment_date)
    dose4_valid = a_copy['Datum_Ctvrta_davka'].notna() & (a_copy['Datum_Ctvrta_davka'] <= enrollment_date)
    
    # Start with dose group 0 for everyone
    a_copy['dose_group'] = 0
    
    # Assign higher dose groups based on valid doses (order matters!)
    a_copy.loc[dose1_valid, 'dose_group'] = 1
    a_copy.loc[dose2_valid, 'dose_group'] = 2  
    a_copy.loc[dose3_valid, 'dose_group'] = 3
    a_copy.loc[dose4_valid, 'dose_group'] = 4
    print(f"  Dose group assignment complete.")
    
    dose_groups = [0, 1, 2, 3, 4]
    # Compute population base: count of people in each (born, dose_group)
    print(f"  Computing population base...")
    pop_base = a_copy.groupby(['born', 'dose_group']).size().reset_index(name='pop')
    # Compute deaths per (week, born, dose_group)
    print(f"  Computing deaths per week/born/dose_group...")
    deaths = a_copy[a_copy['death_date_lpz'].notnull()].groupby(['week', 'born', 'dose_group']).size().reset_index(name='dead')
    # Get all weeks in the study period (from min to max week in the data, not just those with deaths)
    # Use all first and last death dates, plus all dose dates, to get the full week range
    print(f"  Computing week range for study period...")
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
    print(f"    Week range: {min_year}-{min_week:02d} to {max_year}-{max_week:02d}")
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
    print(f"  Building output DataFrame structure...")
    index = pd.MultiIndex.from_product([all_weeks, cohorts], names=['week', 'born'])
    # Prepare output DataFrame
    out = pd.DataFrame(index=index)
    
    print(f"  Processing dose groups...")
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
    print(f"  Computing population attrition from deaths...")
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
    
    # ASMR calculation - scale death counts DOWN based on standard population
    print(f"  Computing ASMR (Age-Standardized Mortality Rates)...")
    asmr_rows = []
    
    for week in all_weeks:
        # print(f"    Processing ASMR for week {week}...")
        week_data = out[out['week'] == week].copy()
        
        # Filter to reasonable birth years only (1920+)
        current_year = int(week[:4])
        week_data = week_data[(week_data['born'] >= 1920) & (week_data['born'] <= current_year - 18)]
        
        if len(week_data) == 0:
            continue
            
        # Calculate age for each birth cohort in this week
        week_data['age'] = week_data['born'].apply(lambda born: approx_age_from_born(pd.to_datetime(week + '-1', format='%G-%V-%u'), born))
        week_data['age_group'] = week_data['age'].apply(age_to_group)
        
        # Remove rows with invalid age groups
        week_data = week_data[week_data['age_group'].notna()]
        
        if len(week_data) == 0:
            continue
        
        asmr_row = {'week': week, 'born': 0}  # Use 0 for ASMR identifier
        
        # Calculate the full US 2000 standard population total
        full_standard_pop = sum(US_2000_STANDARD_POP.values())  # ~275,000
        
        for d in dose_groups:
            total_scaled_deaths = 0
            
            # Group by age group and sum populations/deaths
            age_summary = week_data.groupby('age_group').agg({
                f'{d}_pop': 'sum',
                f'{d}_dead': 'sum'
            }).reset_index()
            
            for _, row in age_summary.iterrows():
                age_group = row['age_group']
                actual_pop = row[f'{d}_pop']
                actual_deaths = row[f'{d}_dead']
                
                if age_group in US_2000_STANDARD_POP and actual_pop > 0:
                    standard_pop = US_2000_STANDARD_POP[age_group]
                    
                    # Scale factor should be <= 1.0 (scaling DOWN)
                    scale_factor = min(1.0, standard_pop / actual_pop)
                    scaled_deaths = actual_deaths * scale_factor
                    
                    total_scaled_deaths += scaled_deaths
            
            # Store the scaled death count (not a rate)
            asmr_row[f'{d}_dead'] = int(round(total_scaled_deaths))
            asmr_row[f'{d}_pop'] = full_standard_pop  # Same for all dose groups
        
        asmr_rows.append(asmr_row)
    
    # Convert ASMR rows to DataFrame and append
    if asmr_rows:
        asmr_df = pd.DataFrame(asmr_rows)
        out = pd.concat([out, asmr_df], ignore_index=True)
        print(f"    Added {len(asmr_rows)} ASMR rows")
    
    # Write to Excel sheet
    print(f"  Writing to Excel sheet...")
    sheet_name = enroll_date_str.replace('-', '_')
    out.to_excel(excel_writer, sheet_name=sheet_name, index=False)
    print(f"Added sheet {sheet_name} to {excel_out_path}")
    print(f"Completed enrollment date {enroll_date_str} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

# Save the Excel file after all sheets are added
excel_writer.close()
print(f"Wrote all dose group CMRs to {excel_out_path}")
