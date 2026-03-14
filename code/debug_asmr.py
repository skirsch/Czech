import pandas as pd
import numpy as np

# Read a sample of the data to understand the structure
df = pd.read_excel('../analysis/fixed_cohort_cmr_dosegroups.xlsx', sheet_name='2021_13')

# Look at regular birth cohort data (not ASMR)
regular_data = df[df['born'] != 0]

print("Sample of regular data (birth cohorts):")
sample = regular_data[regular_data['week'] == '2021-13'].head(10)
print(sample[['week', 'born', '0_dead', '0_pop', '2_dead', '2_pop']])

print(f"\nWeek 2021-13 statistics:")
week_data = regular_data[regular_data['week'] == '2021-13']
print(f"Total records: {len(week_data)}")
print(f"Max 0_dead: {week_data['0_dead'].max()}")
print(f"Max 2_dead: {week_data['2_dead'].max()}")

print(f"\nSample death rates for week 2021-13:")
week_data = week_data.copy()
week_data['rate_0'] = (week_data['0_dead'] / week_data['0_pop']) * 100000
week_data['rate_2'] = (week_data['2_dead'] / week_data['2_pop']) * 100000
week_data = week_data.replace([np.inf, -np.inf], 0).fillna(0)

print(f"Max rate_0: {week_data['rate_0'].max()}")
print(f"Max rate_2: {week_data['rate_2'].max()}")

# Look at high death counts
high_deaths = week_data[week_data['0_dead'] > 100]
if len(high_deaths) > 0:
    print(f"\nBirth cohorts with >100 deaths in week 2021-13:")
    print(high_deaths[['born', '0_dead', '0_pop', 'rate_0']].head())
