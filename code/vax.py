'''
Analyze the CZ records file which is vaccine record level data.

to do: add count of deaths since last shot if 12 monts. and do for the same for 6 month and 3 months.
'''

import pandas as pd
import csv # for the quoting option on output

def read_csv(file_path="data/CR_records.csv"):
    """
    Processes the CSV file, calculates summary statistics, and returns both dataframes.

    Args:
        file_path (str, optional): Path to the CSV file. Defaults to "../data/ockovani-profese.csv".

    Returns:
        tuple: A tuple containing the original DataFrame and the summary DataFrame.
    """
    print("reading file...")
    selected_cols = ['Pohlavikod', 'Rok_narozeni', 'DatumUmrti', 'Datum_1', 'OckovaciLatka_1', 'Datum_2', 'OckovaciLatka_2',
                     'Datum_3', 'OckovaciLatka_3','Datum_4', 'OckovaciLatka_4']
    new_cols = ['sex', 'yob', 'dod_', 'date_1_', 'type_1', 'date_2_', 'type_2', 'date_3_', 'type_3', 'date_4_', 'type_4']

    # Read the CSV file into a DataFrame
    df = pd.read_csv(file_path, usecols=selected_cols, 
                     dtype={'OckovaciLatka_1':str, 'OckovaciLatka_2':str, 'OckovaciLatka_3':str, 'OckovaciLatka_4':str},
                     parse_dates=['DatumUmrti', 'Datum_1', 'Datum_2', 'Datum_3', 'Datum_4'])
    df.columns = new_cols
    return df

def analyze(df):
    print("analyzing...")
    # Convert datum to datetime for grouping
    # df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')

    # Create a new column for the month-year for each date to keep things manageable for grouping
    # df['month_year'] = df['date'].dt.strftime('%m-%Y')
    for old, new in [('dod_', 'dod'), ('date_1_', 'date_1'), ('date_2_', 'date_2'),('date_3_', 'date_3'), ('date_4_', 'date_4')]:
        df[new] = df[old].dt.strftime('%m-%Y')  

    # Create age column with 5 year age ranges
    df['age'] = ((2024 - df['yob']) // 5) * 5
    df['age'] = df['age'].astype(str) + ' - ' + (df['age'] + 4).astype(str)

    # Define the grouping columns
    group_cols = ['sex', 'age', 'date_1', 'date_2', 'date_3', 'date_4', 'type_1', 'type_2', 'type_3', 'type_4', 'dod'] 

    print("grouping...")
    # Calculate summary statistics (# shots, # comorbidities)
    # include empty values as value (dropna=False)
    summary_df = df.groupby(group_cols, dropna=False).agg(
        shots=('yob', 'size'),  # of people who got that combination 
        # we do NOT want to count total deaths to end of 2022; we use dod as a index parameter for more granularity
        # deaths=('dod', 'count')   # number of deaths for people with that combination 
    ).reset_index()

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
  # add a space to make sure not interpreted as a date
  # df['age']=df['age'].apply(lambda x: f' {x}')   
  
  print("writing file to disk...", filename)
  # make sure strings have quotes around them to ensure excel doesn't interpret 12-15 as a date
  # quoting=csv.QUOTE_NONNUMERIC will quote dates which is a problem
  df.to_csv(filename, index=False, quoting=csv.QUOTE_NONE)

# create the dataframes
df=read_csv() 
df2=analyze(df)
write_df_to_csv(df2, 'data/vax.csv')
