'''
Czech Republic tallied comorbidities (yes or no) for each vaccination given and for 5 year age groups.
Some people think that because overall there were twice as many comorbidities for Moderna vs. Pfizer (per thousand vaccinated), that that 
can explain why Moderna has a higher death rate.

That's just silly. You can't get 100% consistency for every 5 year age range like that.

This program will prove it.

The data is published here: https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19
The 3G csv file you need to download can be found here: https://onemocneni-aktualne.mzcr.cz/api/v2/covid-19/ockovani-profese.csv

reads in a csv file from ../data/ockovani-profese.csv into a dataframe. 
with  selected_cols 
['datum', 'vakcina', 'poradi_davky', 'indikace_chronicke_onemocneni', 'vekova_skupina']

rename the columns to 
['date', 'mfg', 'dose', 'com', 'age']

create a new dataframe with summary statistics for the grouping defined below:

The column names will be:
'month', 'age', 'mfg', 'shots', 'com', 'ratio'

The grouping definition are the first 3 fields which iterate over all the possible values where month 
aggregates everything within the month into that one row.

The sums are the "shots" and "com" columns.

shots column should be a count of the number of rows matching the grouping definition.
com is the sum of the com column for rows matching the grouping definition
ratio is just the ratio of com/shots

return the original dataframe and the dataframe with the summary stats.
'''

import pandas as pd
import csv # for the quoting option on output

def read_csv(file_path="data/ockovani-profese.csv"):
    """
    Processes the CSV file, calculates summary statistics, and returns both dataframes.

    Args:
        file_path (str, optional): Path to the CSV file. Defaults to "../data/ockovani-profese.csv".

    Returns:
        tuple: A tuple containing the original DataFrame and the summary DataFrame.
    """
    print("reading file...")
    selected_cols = ['datum', 'vakcina', 'poradi_davky', 'indikace_chronicke_onemocneni', 'vekova_skupina']
    new_cols = ['date', 'mfg', 'dose', 'com', 'age']

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, usecols=selected_cols, parse_dates=['datum'])
    df.columns = new_cols
    return df

def analyze(df):
    print("analyzing...")
    # Convert datum to datetime for grouping
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    # Create a new column for the month-year
    df['month_year'] = df['date'].dt.strftime('%m-%Y')

    # Define the grouping columns
    group_cols = ['month_year', 'dose', 'age', 'mfg']

    # Calculate summary statistics (# shots, # comorbidities)
    summary_df = df.groupby(group_cols).agg(
        shots=('age', 'size'),  # pick any of group_cols to get count of rows in that group
        com=('com', 'count')   # count number of comorbidities for this grouping combo
    ).reset_index()

    # Convert com to integer is no longer needed since count instead of sum
    # summary_df['com'] = summary_df['com'].astype(int)

    # convert age range to a string because 12-15 look like a date in excel
    # so it will read it as a date if we don't add quotes
    # summary_df['age'] = summary_df['age'].astype(str)
    
    # Calculate ratio
    summary_df['ratio'] = summary_df['com'] / summary_df['shots']
    # need to truncate because excel will make a long fraction into a string
    summary_df['ratio'] = summary_df['ratio'].apply(lambda x: round(x, 6))
    return summary_df

def write_df_to_csv(df1, filename):
  """Writes a pandas DataFrame to a CSV file.

  Args:
    df: The pandas DataFrame to write.
    filename: The name of the CSV file to create.

  """
  # don't muck with the original
  df=df1.copy()   # make a copy so don't muck with the original
  # add a space to make sure not interpreted as a date
  df['age']=df['age'].apply(lambda x: f' {x}')   
  
  print("writing file to disk...", filename)
  # make sure strings have quotes around them to ensure excel doesn't interpret 12-15 as a date
  # quoting=csv.QUOTE_NONNUMERIC will quote dates which is a problem
  df.to_csv(filename, index=False, quoting=csv.QUOTE_NONE)

# create the dataframes
df=read_csv() 
df2=analyze(df)
write_df_to_csv(df2, 'data/comorbidity.csv')
