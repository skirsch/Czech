'''
Write a csv file of groupings for the nursing home data for resident covid cases, covid deaths and all deaths 
grouped by week and state.

Create the file by running the current script.

'''

import pandas as pd
import csv # for the quoting option on output
from datetime import timedelta

source_file_2020="./data/nursing/faclevel_2020.txt"
source_file_2021="./data/nursing/faclevel_2021.txt"
source_file_2022="./data/nursing/faclevel_2022.txt"
source_file_2023="./data/nursing/faclevel_2023.txt"

output_path="./data/nursing_state_week_groups"

def read_nursing_csv(file_paths=[source_file_2020,source_file_2021,source_file_2022,source_file_2023]):
    """
    Processes the CSV file, calculates summary statistics, and returns both dataframes.

    Args:
        file_path (str, optional): Path to the source data file. Defaults to an array of "../data/nursing/faclevel_{year}".

    Returns:
        tuple: A tuple containing the DataFrame containing the 
    """
    print("reading files...")

    selected_cols = ['Week Ending', 'Provider State', 'Residents Weekly Confirmed COVID-19',
                     'Residents Weekly COVID-19 Deaths','Residents Weekly All Deaths', 'Total Number of Occupied Beds',    
                     ]
    
    # Read the data files into a DataFrame
    dfs = []
    for file_path in file_paths:
      df = pd.read_csv(file_path, usecols=selected_cols, 
                      dtype={'Provider State':str},
                      parse_dates=['Week Ending'])
      dfs.append(df)
    
    merged_df = pd.concat(dfs, ignore_index=True)   
    print(merged_df.dtypes)
    #group by week ending and state

    grouped_df = merged_df.groupby(['Week Ending', 'Provider State'], as_index=False).sum()

    # ok so this is our final source dataframe with lots of info.
    # so we can do various groupby analyses on it.
    return grouped_df

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
  
  # make sure strings have quotes around them to ensure excel doesn't interpret 12-15 as a date
  # quoting=csv.QUOTE_NONNUMERIC will quote dates which is a problem
  df.to_csv(filename, index=False, quoting=csv.QUOTE_NONE)

df=read_nursing_csv() 
write_df_to_csv(df, output_path+'.csv')
