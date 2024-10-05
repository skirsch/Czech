# I wrote this code to look at the CR data and compute historgrams for what is in there.
# this only works if the csv.xz file is uncompressed
# this happens in the make process.

import pandas as pd

# Specify the path to your CSV file
csv_filename = "data/CR_records.csv"

def histogram(csv_file):
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file)

    # select the column for dose 1, 2, 3 (start at column 5 and increment by 4 stopping at 14)
    # which are the 3 most interesting doses
    for col in range(5, 14, 4):
        # Calculate the histogram of for the vaccine types
        value_counts = df.iloc[:, col].value_counts()  # Access column 3 using index

        # Print the histogram (number of occurrences for each unique value)
        print(value_counts)

histogram(csv_filename)

"""
Here's the output:

>>> histogram(csv_filename)
<stdin>:3: DtypeWarning: Columns (2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30) have mixed types. Specify dtype option on import or set low_memory=False.
OckovaciLatkaKod_1
CO01    5586979
CO02     526453
CO03     447450
CO04     412314
CO07       5425
CO20       1924
CO09        665
CO08        293
CO12        180
CO14        115
CO16        111
CO21         97
CO11         38
CO10         29
CO23         26
CO15         15
CO05         10
CO13          5
CO19          4
CO22          3
CO17          2
Name: count, dtype: int64
OckovaciLatkaKod_2
CO01    5519975
CO02     517783
CO03     439705
CO07       5098
CO09        300
CO04        271
CO08        230
CO12        178
CO14         94
CO16         92
CO20         67
CO11         39
CO10         29
CO23         25
CO15         16
CO05         10
CO13          4
CO22          2
CO17          2
CO21          2
CO19          2
Name: count, dtype: int64
OckovaciLatkaKod_3
CO01    3747813
CO02     568220
CO09      39250
CO08      11141
CO20       6918
CO04       2463
CO15        862
CO03        433
CO07        291
CO21        197
CO16         64
CO22         25
CO23         16
CO19         12
CO11         12
CO12          9
CO14          3
CO05          2
CO13          1
Name: count, dtype: int6


"""