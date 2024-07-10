import pandas as pd

# Specify the path to your CSV file
csv_filename = "./data/CR_records.csv"

def histogram(csv_file):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    for col in range(5,14, 4):
        # Calculate the histogram of unique values in column 3 (assuming column index is 2)
        value_counts = df.iloc[:, 5].value_counts()  # Access column 3 using index

        # Print the histogram (number of occurrences for each unique value)
        print(value_counts)

histogram(csv_filename)