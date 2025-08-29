# 
#   KCOR.py
#
# Analysis script for CMR for vaccination dose groups
#
# I run it from VS Code (execute the buffer). It takes about 10 minutes to run for each enrollment date.
# Be sure you have pandas, numpy, matplotlib, and seaborn installed in your python environment.
# You can install them with pip if needed:   
#  pip install pandas numpy matplotlib seaborn (or apt install python3-pandas python3-numpy python3-matplotlib python3-seaborn on WSL)

# You can also run it from the command line but be sure you have seaborn installed in your python environment.
# You can install seaborn with pip if needed:   pip install seaborn (or apt install python3-seaborn on WSL)

#   cd code; make KCOR

# Output file:
#   Czech/data/KCOR_output.xlsx (configurable via Makefile, current default)
#
# The output file contains the CMR for each dose group by week, birth cohort, sex, and vaccination status.
# The output file contains multiple sheets, one for each enrollment date.
# The data is structured with Dose as an index column and simplified Alive/Dead value columns.
# Each row represents a unique combination of week, birth cohort, sex, and dose group.
# The output file columns are:
#   ISOweekDied: ISO week (YYYY-WW format, e.g., 2020-10)
#   DateDied: Monday date of the ISO week (YYYY-MM-DD format, e.g., 2020-03-02)
#   YearOfBirth: birth year (e.g., "1970") or "ASMR" for age-standardized rows and "UNK" for unknown birth year
#   Sex: alphabetic code (M=Male, F=Female, O=Other/Unknown)
#   Dose: dose group (0=unvaccinated, 1=1 dose, 2=2 doses, 3=3 doses, 4=4 doses, 5=5 doses, 6=6 doses, 7=7 doses)
#   Alive: population count alive in this dose group
#   Dead: death count in this dose group (age-standardized for ASMR rows with YearOfBirth="ASMR")
#
# The population counts are adjusted for deaths over time (attrition).
#
# The data is then imported into this spreadsheet for analysis.
#   Czech/analysis/fixed_cohort_cmr_dosegroups_analysis.xlsx
#
# This script processes vaccination and death data to compute CMR (Crude Mortality Rate) for each age cohort and vaccination dose group (0, 1, 2, 3, 4, 5, 6, 7). 
# It loads the Czech dataset, processes it to extract relevant information, computes weekly death counts for vaccinated and unvaccinated individuals, and calculates CMR per 100,000 population per year.
# Computes ages for birth year cohorts from 1900 to 2020 using Czech demographic standardization.
# 
# It also shows deaths by birth cohort and vaccination status over time, allowing for analysis of mortality trends in relation to vaccination status.
#
# This creates output files that are analyzed in files in analysis/fixed_cohort_CMR.... files.
#
# This is the main KCOR analysis script. It generates output to allow computation 
# of CMR (Crude Mortality Rate) for dose 0, 1, 2, 3, 4, 5, 6, and 7 by outputting alive and dead counts by week, birth cohort, and vaccination status.
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
# It is a replacement for the old KCOR.py, providing enhanced analysis capabilities with population and death data.
# enabling the the analysis of mortality trends in relation to vaccination status.
# It uses the same data format as the old KCOR.py.
# it does not require the old KCOR.py script to run, but it uses the same data format.
# It only looks at first dose vaccination data and ACM death dates.
#


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

# Czech Reference Population for ASMR calculation (by 5-year birth cohorts)
# Source: Czech demographic data
CZECH_REFERENCE_POP = {
    1900: 13,       # 1900-1904
    1905: 23,       # 1905-1909
    1910: 32,       # 1910-1914
    1915: 45,       # 1915-1919
    1920: 1068,     # 1920-1924
    1925: 9202,     # 1925-1929
    1930: 35006,    # 1930-1934
    1935: 72997,    # 1935-1939
    1940: 150323,   # 1940-1944
    1945: 246393,   # 1945-1949
    1950: 297251,   # 1950-1954
    1955: 299766,   # 1955-1959
    1960: 313501,   # 1960-1964
    1965: 335185,   # 1965-1969
    1970: 415319,   # 1970-1974
    1975: 456701,   # 1975-1979
    1980: 375605,   # 1980-1984
    1985: 357674,   # 1985-1989
    1990: 338424,   # 1990-1994
    1995: 256900,   # 1995-1999
    2000: 251049,   # 2000-2004
    2005: 287094,   # 2005-2009
    2010: 275837,   # 2010-2014
    2015: 238952,   # 2015-2019
    2020: 84722,    # 2020-2024
}

# Age bins for ASMR (Age-Standardized Mortality Rate) computation
# These bins are used to group individuals by age for standardization against Czech reference population
# Aligned with 5-year cohorts to match Czech demographic data (birth years 1900-2020)
AGE_BINS = [
    ("0-4",   0,   4),    # ages 0-4 years (aligned with 5-year cohorts)
    ("5-9",   5,   9),
    ("10-14", 10, 14),
    ("15-19", 15, 19),
    ("20-24", 20, 24),
    ("25-29", 25, 29),
    ("30-34", 30, 34),
    ("35-39", 35, 39),
    ("40-44", 40, 44),
    ("45-49", 45, 49),
    ("50-54", 50, 54),
    ("55-59", 55, 59),
    ("60-64", 60, 64),
    ("65-69", 65, 69),
    ("70-74", 70, 74),
    ("75-79", 75, 79),
    ("80-84", 80, 84),
    ("85-89", 85, 89),
    ("90-94", 90, 94),
    ("95-99", 95, 99),
    ("100-104", 100, 104),
    ("105-109", 105, 109),
    ("110-114", 110, 114),
    ("115-119", 115, 119),
    ("120-124", 120, 124),
    ("125+", 125, 200),   # cap at 200 for very old ages
]

def age_to_group(age_years: int) -> str:
    """Map integer age to age group label for ASMR calculation.
    
    Used in ASMR (Age-Standardized Mortality Rate) computation to group individuals
    by age before applying Czech reference population standardization.
    """
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

def birth_year_to_age_at_week(birth_year: int, week_date) -> int:
    """Calculate age at specific week date from birth year."""
    if pd.isna(birth_year) or birth_year == -1:
        return None
    return approx_age_from_born(week_date, birth_year)

def get_czech_reference_pop_for_birth_year(birth_year: int) -> int:
    """Get Czech reference population count for a specific birth year by mapping to 5-year cohort."""
    if pd.isna(birth_year) or birth_year < 1900:
        return 0
    
    # Map birth year to 5-year cohort (1900-1904 -> 1900, 1905-1909 -> 1905, etc.)
    cohort_year = ((birth_year - 1900) // 5) * 5 + 1900
    return CZECH_REFERENCE_POP.get(cohort_year, 0)

# define the output Excel file path
# This will contain the CMR for each dose group by week, birth cohort, and vaccination status.
# This is used to compute the HR (Hazard Ratio) for each dose group by week, birth cohort, and vaccination status
# and it eliminates any HVE bias since it doesn't compare vaccinated to unvaccinated.
if len(sys.argv) >= 2:
    excel_out_path = sys.argv[1]
else:
    excel_out_path = "../data/KCOR_output.xlsx"  # default fallback
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

# rename the columns in English (same as KCOR.py)
a.columns = [
    'ID', 'Infection', 'Sex', 'YearOfBirth', 'DateOfPositiveTest', 'DateOfResult', 'Recovered', 'Date_COVID_death',
    'Symptom', 'TestType', 'Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose',
    'Date_FifthDose', 'Date_SixthDose', 'Date_SeventhDose', 'VaccineCode_FirstDose', 'VaccineCode_SecondDose',
    'VaccineCode_ThirdDose', 'VaccineCode_FourthDose', 'VaccineCode_FifthDose', 'VaccineCode_SixthDose',
    'VaccineCode_SeventhDose', 'PrimaryCauseHospCOVID', 'bin_Hospitalization', 'min_Hospitalization',
    'days_Hospitalization', 'max_Hospitalization', 'bin_ICU', 'min_ICU', 'days_ICU', 'max_ICU', 'bin_StandardWard',
    'min_StandardWard', 'days_StandardWard', 'max_StandardWard', 'bin_Oxygen', 'min_Oxygen', 'days_Oxygen',
    'max_Oxygen', 'bin_HFNO', 'min_HFNO', 'days_HFNO', 'max_HFNO', 'bin_MechanicalVentilation_ECMO',
    'min_MechanicalVentilation_ECMO', 'days_MechanicalVentilation_ECMO', 'max_MechanicalVentilation_ECMO',
    'Mutation', 'DateOfDeath', 'Long_COVID', 'DCCI']

# if you got infected more than once, it will create a duplicate record (with a different ID) so
# remove those records so we don't double count the deaths.

# Remove records where Infection > 1
a = a[(a['Infection'].fillna(0).astype(int) <= 1)]

# Convert Sex to alphabetic codes: M, F, O
def sex_to_alpha(sex_val):
    if pd.isna(sex_val) or sex_val == '':
        return 'O'  # Other/Unknown
    elif str(sex_val) == '1':
        return 'M'  # Male
    elif str(sex_val) == '2':
        return 'F'  # Female
    else:
        return 'O'  # Other/Unknown

a['Sex'] = a['Sex'].apply(sex_to_alpha)

# Debug: Check data quality after Sex conversion
print(f"Records after Sex conversion: {len(a)}")
print(f"Sex distribution: {a['Sex'].value_counts()}")



# Convert relevant columns to datetime (ISO format assumed: YYYY-MM-DD)
# Extract cohort year from birth year range (e.g., '1970-1974' -> 1970)
a['birth_year'] = a['YearOfBirth'].str.extract(r'(\d{4})').astype(float)
# Limit to cohorts born 1900-2020
# This will also convert NaN birth years to NaN, which we can handle later
## Remove birth year filtering so all birthdates, including blanks, are included

# Parse ISO week format for death date only (first_dose_date will be parsed later)
a['DateOfDeath'] = pd.to_datetime(a['DateOfDeath'].str.replace(r'[^0-9-]', '', regex=True) + '-1', format='%G-%V-%u', errors='coerce')
# Keep WeekOfDeath in original ISO week format (YYYY-WW) for exact matching
a['WeekOfDeath'] = a['DateOfDeath'].dt.strftime('%G-%V')
# Set WeekOfDeath to NaN for invalid death dates
a.loc[a['DateOfDeath'].isna(), 'WeekOfDeath'] = pd.NA

# Debug: Check death data quality
print(f"Total records: {len(a)}")
print(f"Records with deaths: {a['DateOfDeath'].notnull().sum()}")
print(f"Records with valid WeekOfDeath: {a['WeekOfDeath'].notna().sum()}")

# Extract year from birth_year string (first 4 chars)
a['birth_year'] = a['birth_year'].astype(str).str[:4]
a['birth_year'] = pd.to_numeric(a['birth_year'], errors='coerce')

# --------- Parse all dose dates ONCE before the enrollment loop ---------
print(f"Parsing dose date columns (one time only)...")
# Add dose date columns if not already present
for col in ['Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose', 'Date_FifthDose', 'Date_SixthDose', 'Date_SeventhDose']:
    if col not in a.columns:
        a[col] = pd.NaT

# Use the fast vectorized ISO week parsing approach (same as KCOR.py)
dose_date_columns = ['Date_FirstDose', 'Date_SecondDose', 'Date_ThirdDose', 'Date_FourthDose', 'Date_FifthDose', 'Date_SixthDose', 'Date_SeventhDose']
for col in dose_date_columns:
    print(f"  Parsing {col}...")
    # Fast vectorized ISO week parsing: YYYY-WW + '-1' -> datetime (keep as Timestamp, not .date)
    a[col] = pd.to_datetime(a[col] + '-1', format='%G-%V-%u', errors='coerce')
print(f"Dose date parsing complete for all columns.")

# Fix death dates - now we can compare properly since all dates are pandas Timestamps
## Only use LPZ death date, ignore other death date
a = a[~((a['DateOfDeath'].notnull()) & (a['Date_FirstDose'] > a['DateOfDeath']))]

# Convert birth years to integers once (outside the enrollment loop)
print(f"Converting birth years to integers (one time only)...")
a['YearOfBirth'] = a['birth_year'].apply(lambda x: int(x) if pd.notnull(x) else -1)
print(f"Birth year conversion complete.")

# --------- NEW: Dose group analysis for multiple enrollment dates ---------

### YOU CAN RESTART HERE if code bombs out. This saves time.

# Dose date columns
dose_date_cols = [
    (0, None),
    (1, 'Date_FirstDose'),
    (2, 'Date_SecondDose'),
    (3, 'Date_ThirdDose'),
    (4, 'Date_FourthDose'),
    (5, 'Date_FifthDose'),
    (6, 'Date_SixthDose'),
    (7, 'Date_SeventhDose'),
]

for enroll_date_str in enrollment_dates:
    # Parse ISO week string as Monday of that week
    import datetime
    print(f"Processing enrollment date {enroll_date_str} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    enrollment_date = pd.to_datetime(enroll_date_str + '-1', format='%G-%V-%u', errors='coerce')
    print(f"  Creating copy of dataset ({len(a)} records)...")
    a_copy = a.copy()
    print(f"  Keeping all records including deaths before enrollment date...")
    # Keep all individuals, including those who died before the enrollment date
    # This allows us to see pre-enrollment deaths in their correct dose groups
    print(f"  Records in analysis: {len(a_copy)}")
    
    # Assign dose group as of enrollment date (highest dose <= enrollment date) - VECTORIZED VERSION
    # For people who died before enrollment, use their death date instead of enrollment date
    print(f"  Assigning dose groups...")
    
    # For each person, determine the reference date for dose group assignment
    # If they died before enrollment, use death date; otherwise use enrollment date
    reference_dates = a_copy['DateOfDeath'].where(
        a_copy['DateOfDeath'].notna() & (a_copy['DateOfDeath'] < enrollment_date),
        enrollment_date
    )
    
    # Create boolean masks for each dose being valid (not null and <= reference_date)
    dose1_valid = a_copy['Date_FirstDose'].notna() & (a_copy['Date_FirstDose'] <= reference_dates)
    dose2_valid = a_copy['Date_SecondDose'].notna() & (a_copy['Date_SecondDose'] <= reference_dates)
    dose3_valid = a_copy['Date_ThirdDose'].notna() & (a_copy['Date_ThirdDose'] <= reference_dates)
    dose4_valid = a_copy['Date_FourthDose'].notna() & (a_copy['Date_FourthDose'] <= reference_dates)
    dose5_valid = a_copy['Date_FifthDose'].notna() & (a_copy['Date_FifthDose'] <= reference_dates)
    dose6_valid = a_copy['Date_SixthDose'].notna() & (a_copy['Date_SixthDose'] <= reference_dates)
    dose7_valid = a_copy['Date_SeventhDose'].notna() & (a_copy['Date_SeventhDose'] <= reference_dates)
    
    # Start with dose group 0 for everyone
    a_copy['dose_group'] = 0
    
    # Assign higher dose groups based on valid doses (order matters!)
    a_copy.loc[dose1_valid, 'dose_group'] = 1
    a_copy.loc[dose2_valid, 'dose_group'] = 2  
    a_copy.loc[dose3_valid, 'dose_group'] = 3
    a_copy.loc[dose4_valid, 'dose_group'] = 4
    a_copy.loc[dose5_valid, 'dose_group'] = 5
    a_copy.loc[dose6_valid, 'dose_group'] = 6
    a_copy.loc[dose7_valid, 'dose_group'] = 7
    print(f"  Dose group assignment complete.")
    
    dose_groups = [0, 1, 2, 3, 4, 5, 6, 7]
    # Compute population base: count of people in each (born, sex, dose_group)
    print(f"  Computing population base...")
    pop_base = a_copy.groupby(['YearOfBirth', 'Sex', 'dose_group']).size().reset_index(name='pop')
    print(f"    Total population across all dose groups: {pop_base['pop'].sum()}")
    
    # Compute deaths per (WeekOfDeath, born, sex, dose_group)
    print(f"  Computing deaths per WeekOfDeath/born/sex/dose_group...")
    deaths = a_copy[a_copy['DateOfDeath'].notnull() & a_copy['WeekOfDeath'].notna()].groupby(['WeekOfDeath', 'YearOfBirth', 'Sex', 'dose_group']).size().reset_index(name='dead')
    print(f"    Total deaths across all dose groups: {deaths['dead'].sum()}")
    print(f"    Unique weeks with deaths: {len(deaths['WeekOfDeath'].unique())}")
    # Get all weeks in the study period (from database start to end, including pre-enrollment period)
    # Use all vaccination and death dates to get the full week range
    print(f"  Computing week range for entire study period (including pre-enrollment)...")
    all_dates = pd.concat([
        a_copy['Date_FirstDose'],
        a_copy['Date_SecondDose'],
        a_copy['Date_ThirdDose'],
        a_copy['Date_FourthDose'],
        a_copy['Date_FifthDose'],
        a_copy['Date_SixthDose'],
        a_copy['Date_SeventhDose'],
        a_copy['DateOfDeath']
    ]).dropna()
    min_week = all_dates.min().isocalendar().week
    min_year = all_dates.min().isocalendar().year
    max_week = all_dates.max().isocalendar().week
    max_year = all_dates.max().isocalendar().year
    print(f"    Full week range: {min_year}-{min_week:02d} to {max_year}-{max_week:02d} (includes pre-enrollment period)")
    # Build all weeks between min and max
    from datetime import date, timedelta
    def week_year_iter(y1, w1, y2, w2):
        d = date.fromisocalendar(y1, w1, 1)
        dend = date.fromisocalendar(y2, w2, 1)
        while d <= dend:
            yield d.isocalendar()[:2]
            # next week
            d += timedelta(days=7)
    all_weeks = [f"{y}-{w:02d}" for y, w in week_year_iter(min_year, min_week, max_year, max_week)]
    cohorts = sorted(a_copy['YearOfBirth'].dropna().unique())
    sexes = sorted(a_copy['Sex'].dropna().unique())
    
    # Build MultiIndex for all (WeekOfDeath, born, sex, dose)
    print(f"  Building output DataFrame structure...")
    index = pd.MultiIndex.from_product([all_weeks, cohorts, sexes, dose_groups], names=['ISOweekDied', 'YearOfBirth', 'Sex', 'Dose'])
    # Prepare output DataFrame
    out = pd.DataFrame(index=index)
    
    print(f"  Processing dose groups...")
    # Initialize Alive and Dead columns
    out['Alive'] = 0
    out['Dead'] = 0
    
    for d in dose_groups:
        # deaths for this group
        deaths_d = deaths[deaths['dose_group'] == d].set_index(['WeekOfDeath', 'YearOfBirth', 'Sex'])['dead']
        # pop for this group (initial for all weeks)
        pop_d = pop_base[pop_base['dose_group'] == d].set_index(['YearOfBirth', 'Sex'])['pop']
        
        # Fill data for this dose group
        for week in all_weeks:
            for cohort in cohorts:
                for sex in sexes:
                    # Get population count
                    pop_count = pop_d.get((cohort, sex), 0)
                    out.loc[(week, cohort, sex, d), 'Alive'] = pop_count
                    
                    # Get death count
                    death_count = deaths_d.get((week, cohort, sex), 0)
                    out.loc[(week, cohort, sex, d), 'Dead'] = death_count

    out = out.reset_index()
    out['ISOweekDied'] = out['ISOweekDied'].astype(str)
    
    # Convert YearOfBirth to meaningful strings
    out['YearOfBirth'] = out['YearOfBirth'].apply(lambda x: 'UNK' if x == -1 else ('ASMR' if x == 0 else str(x)))
    
    out['Sex'] = out['Sex'].astype(str)
    out['Dose'] = out['Dose'].astype(int)
    
    # Add a readable date column (Monday of the ISO week) right after ISOweekDied
    out['DateDied'] = out['ISOweekDied'].apply(lambda week: pd.to_datetime(week + '-1', format='%G-%V-%u').strftime('%Y-%m-%d'))
    
    # Reorder columns to put DateDied right after ISOweekDied
    cols = ['ISOweekDied', 'DateDied', 'YearOfBirth', 'Sex', 'Dose', 'Alive', 'Dead']
    out = out[cols]

    # Overwrite population columns to reflect attrition from deaths (vectorized)
    print(f"  Computing population attrition from deaths...")
    out = out.sort_values(['YearOfBirth', 'Sex', 'Dose', 'ISOweekDied'])
    
    for (YearOfBirth, Sex, Dose), group in out.groupby(['YearOfBirth', 'Sex', 'Dose']):
        pop = group['Alive'].values.astype(int)
        dead = group['Dead'].values.astype(int)
        alive = np.empty_like(pop)
        alive[0] = pop[0]
        for i in range(1, len(pop)):
            alive[i] = max(alive[i-1] - dead[i-1], 0)
        out.loc[group.index, 'Alive'] = alive
    
    # ASMR calculation - scale death counts DOWN based on standard population
    print(f"  Computing ASMR (Age-Standardized Mortality Rates)...")
    asmr_rows = []
    
    for week in all_weeks:
        week_data = out[out['ISOweekDied'] == week].copy()
        # Filter to reasonable birth years only (1900-2020, those in Czech reference population)
        current_year = int(week[:4])
        week_data = week_data[week_data['YearOfBirth'].apply(lambda x: str(x).isdigit() and 1900 <= int(x) <= 2020)]
        if len(week_data) == 0:
            continue
        # Calculate age for each birth cohort in this week
        week_date = pd.to_datetime(week + '-1', format='%G-%V-%u')  # Convert ISO week back to Monday date
        week_data['age'] = week_data['YearOfBirth'].apply(lambda YearOfBirth: approx_age_from_born(week_date, int(YearOfBirth)) if str(YearOfBirth).isdigit() else None)
        week_data['age_group'] = week_data['age'].apply(age_to_group)
        # Remove rows with invalid age groups
        week_data = week_data[week_data['age_group'].notna()]
        if len(week_data) == 0:
            continue
        
        # Calculate the full Czech reference population total
        full_standard_pop = sum(CZECH_REFERENCE_POP.values())  # Czech reference population total
        
        for d in dose_groups:
            dose_data = week_data[week_data['Dose'] == d]
            if len(dose_data) == 0:
                continue
            
            # Group by sex and sum across age groups for this dose
            sex_summary = dose_data.groupby('Sex').agg({
                'Alive': 'sum',
                'Dead': 'sum'
            }).reset_index()
            
            for _, sex_row in sex_summary.iterrows():
                sex_val = sex_row['Sex']
                total_alive = sex_row['Alive']
                total_dead = sex_row['Dead']
                
                total_scaled_deaths = 0
                
                # Now calculate birth-year-standardized deaths for this sex/dose combination
                dose_sex_data = dose_data[dose_data['Sex'] == sex_val]
                birth_year_summary = dose_sex_data.groupby('YearOfBirth').agg({
                    'Alive': 'sum',
                    'Dead': 'sum'
                }).reset_index()
                
                for _, row in birth_year_summary.iterrows():
                    birth_year_str = row['YearOfBirth']
                    actual_pop = row['Alive']
                    actual_deaths = row['Dead']
                    
                    # Convert birth year string to int and map to 5-year cohort
                    if str(birth_year_str).isdigit():
                        birth_year = int(birth_year_str)
                        # Map to 5-year cohort (1900-1904 -> 1900, 1905-1909 -> 1905, etc.)
                        cohort_year = ((birth_year - 1900) // 5) * 5 + 1900
                        
                        if cohort_year in CZECH_REFERENCE_POP and actual_pop > 0:
                            reference_pop = CZECH_REFERENCE_POP[cohort_year]
                            
                            # Scale to match reference population (up or down as needed)
                            scale_factor = reference_pop / actual_pop
                            scaled_deaths = actual_deaths * scale_factor
                            
                            total_scaled_deaths += scaled_deaths
                
                # Create ASMR row for this sex/dose combination
                asmr_row = {
                    'ISOweekDied': week, 
                    'YearOfBirth': 'ASMR',  # Use 'ASMR' string instead of 0
                    'Sex': sex_val,         # Preserve original sex
                    'Dose': d,              # Preserve original dose number
                    'Alive': full_standard_pop,
                    'Dead': int(round(total_scaled_deaths))
                }
                asmr_rows.append(asmr_row)
    
    # Convert ASMR rows to DataFrame and append
    if asmr_rows:
        asmr_df = pd.DataFrame(asmr_rows)
        # Add DateDied column to ASMR rows
        asmr_df['DateDied'] = asmr_df['ISOweekDied'].apply(lambda week: pd.to_datetime(week + '-1', format='%G-%V-%u').strftime('%Y-%m-%d'))
        # Reorder columns to match main DataFrame
        asmr_df = asmr_df[['ISOweekDied', 'DateDied', 'YearOfBirth', 'Sex', 'Dose', 'Alive', 'Dead']]
        
        out = pd.concat([out, asmr_df], ignore_index=True)
        print(f"    Added {len(asmr_rows)} ASMR rows")
    
    # Write to Excel sheet
    print(f"  Writing to Excel sheet...")
    sheet_name = enroll_date_str.replace('-', '_')
    out.to_excel(excel_writer, sheet_name=sheet_name, index=False)
    
    # Format YearOfBirth column as text to avoid Excel warnings
    workbook = excel_writer.book
    worksheet = excel_writer.sheets[sheet_name]
    # the following line is commented out because it simply didn't work. Excel flags the YearOfBirth column as numbers anyway so you have to ignore the warning in Excel and save.
    # text_format = workbook.add_format({'num_format': '@'})  # '@' = text format
    # worksheet.set_column('C:C', None, text_format)  # Column C is YearOfBirth
    
    print(f"Added sheet {sheet_name} to {excel_out_path}")
    print(f"Completed enrollment date {enroll_date_str} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

# Save the Excel file after all sheets are added
excel_writer.close()
print(f"Wrote all dose group CMRs to {excel_out_path}")
