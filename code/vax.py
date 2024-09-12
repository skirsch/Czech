'''
Analyze the CZ records file which is vaccine record level data.

Creates 4 csv files:

1. death by month which uses month of death (month_of_death) as grouping criteria
2. within 365 days of FIRST shot which doesn't use month_of_death as grouping and will count deaths within 365 days of shot
3. same as 2, but with YOB column instead of 5 year age range
Shot 4 is useless... too late in the year
4. Age, date of shot 2, brand of shot 2, batch of shot 2 : number of deaths within various timeframes from time of shot

'''

import pandas as pd
import csv # for the quoting option on output
from datetime import timedelta

# time window for deaths in summary stats
# so we can compare deaths for 90, 180, 270, etc. days from FIRST shot
thresholds=[90, 180, 270, 365, 455, 545, 635, 730]
source_file="../data/CR_records.csv"
output_path="../data/vax_"
# test this using _10K.csv which is shorter
# run the Makefile from the cdoe directory since this is hardwired
def read_csv(file_path=source_file):
    """
    Processes the CSV file, calculates summary statistics, and returns both dataframes.

    Args:
        file_path (str, optional): Path to the CSV file. Defaults to "../data/ockovani-profese.csv".

    Returns:
        tuple: A tuple containing the original DataFrame and the summary DataFrame.
    """
    print("reading file...")
    selected_cols = ['Pohlavikod', 'Rok_narozeni', 'DatumUmrti', # sex, YOB, DOD,
                     'Datum_1', 'Sarze_1', 'OckovaciLatka_1',    # date of shot, batchID, BrandID
                     'Datum_2', 'Sarze_2', 'OckovaciLatka_2',
                     'Datum_3', 'Sarze_3', 'OckovaciLatka_3']
    
    # the date_ columns (shot dates and the death date) are actual date objects which I later convert to strings in a later phase.
    # Note the parse_dates argument to the read_csv.
    # new_cols must be exactly lined up to the list of selected columns
    new_cols = ['sex', 'yob', 'dod_', 
                'date_1_', 'batch_1', 'brand_1', 
                'date_2_', 'batch_2', 'brand_2', 
                'date_3_', 'batch_3', 'brand_3']

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, usecols=selected_cols, 
                     dtype={'OckovaciLatka_1':str, 'OckovaciLatka_2':str, 'OckovaciLatka_3':str,
                            'Sarze_1': str, 'Sarze_2': str, 'Sarze_3': str
                            },
                     parse_dates=['DatumUmrti', 'Datum_1', 'Datum_2', 'Datum_3'])
    # rename the columns
    df.columns = new_cols
    shot_batch_cols = ['batch_1', 'batch_2', 'batch_3']
    
    # now need to upper case everything and remove leading and trailing spaces
    for col in shot_batch_cols:
      df[col] = df[col].str.strip().str.upper()

    print("adding death columns...")
    # add shot death stats from last date of shot BEFORE we do the grouping!
    # these are all pure date columns (not month year)
    shot_date_cols = ['date_1_', 'date_2_', 'date_3_']
    
    dod_col='dod_'  
   
    # add some more death columns to our source dataframe
    add_death_cols(df, dod_col, shot_date_cols)

    # return a df suitable for analysis (grouping)

    # Convert datum to datetime for grouping
    # df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    # Create a new column for the month-year for EACH date to keep things manageable for grouping
    # since grouping by single data would be overwhelming
    # df['month_year'] = df['date'].dt.strftime('%m-%Y')
    for old, new in [('dod_', 'month_of_death'), ('date_1_', 'date_1'), ('date_2_', 'date_2'),('date_3_', 'date_3')]:
        df[new] = df[old].dt.strftime('%m-%Y')  

    # Create age column with 5 year age ranges
    # So grouping by age creates fewer categories in the index
    df['age'] = ((2024 - df['yob']) // 5) * 5
    df['age'] = df['age'].astype(str) + ' - ' + (df['age'] + 4).astype(str)

    # ok so this is our final source dataframe with lots of info.
    # so we can do various groupby analyses on it.
    return df

def add_death_cols(df, dod_col, shot_date_cols):
  """Counts deaths within specific timeframes after shot dates.

  Args:
    df: The pandas DataFrame.
    group_cols: A list of columns to group by.
    dod_col: The name of the death of death column.
    shot_date_cols: A list of shot date columns.

  Returns:
    A pandas DataFrame with counts for different timeframes.
  """

  # Create a helper column for max shot date so can easily compute the days since death
  # Don't use this... Need to do death computation relative to a SPECIFIC SHOT NUMBER 
  # df['max_shot_date'] = df[shot_date_cols].max(axis=1)

  # days until death column (based on the first shot date)

  # First, if you are NOT vaccinated, then let's pretend your vax date is Jan 1, 2020
  # and we'll set the type to UNVAXXED. fillna means fill only if empty.
  df['date_1_'] = df['date_1_'].fillna(pd.Timestamp('2020-01-01'))
  df['brand_1'] = df['brand_1'].fillna('UNVAXXED')

  # now compute death outcomes for doses 1 to 3
  for dose in range(1,4):
    df[f'days_until_death_from_d{dose}'] = (df[dod_col] - df[f'date_{dose}_']).dt.days.round(0)

    # now create boolean columns for each record indicating where the death was (90 days, 180 days, etc.)
    for threshold in thresholds:
      df[f'death_within_{threshold}d_d{dose}'] = df[f'days_until_death_from_d{dose}'] <= threshold

  # Group by specified columns and sum the boolean columns
  # result = df.groupby(group_cols)[['death_within_3m', 'death_within_6m', 'death_within_9m', 'death_within_12m']].sum().reset_index()
  return df

def analyze(df, group_cols):
    # this function basically does the groupings and adds the count column(s) for the two different
    # output styles vax1 and vax2.
    # vax1 output includes month of death, so lots more rows in the group
    # vax2 output appends on deaths during various timeframes from the shot
    # vax3 is like vax2, but with single digit age ranges
    # print("grouping by", group_cols)
    # Define the grouping columns

    # Normally, we are looking at 1 year mortality from time of shot
    # But if month_of_death is included in the index, we just outout the # of people who have that combination in the index

    if 'month_of_death' in group_cols:
      # Calculate summary statistics (# shots, # comorbidities)
      # Important to include empty values as a permissiable value for the index (e.g., third shot is blank) (dropna=False)
      # specifying dropna is critical so we get all combos, not just people who got 3 shots!
      summary_df = df.groupby(group_cols, dropna=False).agg(
        count_of_dead_or_survived=('yob', 'size')  # of people who got that exact combination 
        # CAUTION!!! If the index has a date of death filled in, count=# deaths
        # if the index has NO date of death, then these are people who got shot who did NOT die
        # i.e., who survived
        # to find the total number of people who got shot that month, you must add up all the alive
        # people and all the dead people who got shot in that month. It's tricky!

      ).reset_index()
    else:
      # OK, month of death isn't in group by, so this is our chance to create columns for deaths 
      # count number of people who died within N months of the most recent shot in this row

      # This is the normal case. The index is computed and we output at the number of people who died within N months of
      # the shot for that combination.

      print("grouping and calculating deaths within N months for various N")
      # Group by specified columns and calculate counts and total
      summary_df = df.groupby(group_cols, dropna=False).agg(
        shots=('yob', 'size'),  # this is # shots given (size of the group identified by the index)
        # now add additional columns for dose 1 thresholds, then dose 2 thresholds, etc.
        **{f'deaths_within_{threshold}d_d{dose}': (f'death_within_{threshold}d_d{dose}', 'sum') 
           for dose in range(1,4) 
           for threshold in thresholds  # thresholds will vary the fastest
          } 
        ).reset_index()
      
      # print("done grouping...")

    # Convert com to integer is no longer needed since count instead of sum
    # summary_df['com'] = summary_df['com'].astype(int)

    # convert age range to a string because 12-15 look like a date in excel
    # so it will read it as a date if we don't add quotes
    # summary_df['age'] = summary_df['age'].astype(str)
    
    # Calculate ratio
    # summary_df['ratio'] = summary_df['com'] / summary_df['shots']
    # need to truncate because excel will make a long fraction into a string
    # summary_df['ratio'] = summary_df['ratio'].apply(lambda x: round(x, 6))

    return summary_df

def write_df_to_csv(df1, filename):
  """Writes a pandas DataFrame to a CSV file.

  Args:
    df: The pandas DataFrame to write.
    filename: The name of the CSV file to create.

  """
  # don't muck with the original
  df=df1.copy()   # make a copy so don't muck with the original
  # if there is an age column, add a space in front of the age to make sure not interpreted as a date by excel
  
  print("writing file to disk...", filename)

  # if we're outputting an age column, modify it for excel by adding a space before each value so not interpreted as date
  if 'age' in df.columns:
    df['age']=df['age'].apply(lambda x: f' {x}')   
  
  # make sure strings have quotes around them to ensure excel doesn't interpret 12-15 as a date
  # quoting=csv.QUOTE_NONNUMERIC will quote dates which is a problem
  df.to_csv(filename, index=False, quoting=csv.QUOTE_NONE)

# define the grouping columns for each of the CSV files I will output 
# the first one adds months of death to allow for analysis restricting months of deaths, e.g., to low COVID months
group_cols = (['sex', 'age', 'date_1', 'date_2', 'date_3', 'brand_1', 'brand_2', 'brand_3', 'month_of_death'],  # add month of death to group
              ['sex', 'age', 'date_1', 'date_2', 'date_3', 'brand_1', 'brand_2', 'brand_3'], # outputs mortality at N months after the shot
              ['sex', 'yob', 'date_1', 'date_2', 'date_3', 'brand_1', 'brand_2', 'brand_3'], # YOB instead of date range (so more detailed)
              ['age', 'brand_2', 'batch_2', 'date_2']) # BATCH SAFETY ANALYSIS. This is by 5 year age range, mfg, batch, and month of injection 


# Start executing here
# Note that the input filename is hardcoded
# read_csv will read in the file, change column names, add the death columns (for up to three doses)
# so we will be set up for various groupings
df=read_csv() 

# analyze two ways: one allows you to filter on death month, 
# the other computes leaves the death month out of the group and sums the death count for 3,6,9,12 months after the shot () plus avg days until death
suffix=1

# write out two .csv files: one for month of deeath in the index (for granualar analysis)
# and one where we count the deaths in first 90, 180, etc. days since the shot given to a person in the group
for cols in group_cols:
  df2=analyze(df, cols)
  write_df_to_csv(df2, output_path+str(suffix)+'.csv')
  suffix+=1
