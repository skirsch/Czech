#!/usr/bin/env python3
"""
Debug script to examine the actual columns and data
"""

import pandas as pd
import numpy as np

def main():
    try:
        df = pd.read_excel('../analysis/KCOR_analysis.xlsx', sheet_name='2021_24_BY1940_D2v0_KCOR')
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check if KCOR and KCOR_raw are actually different
        print(f"\nKCOR equals KCOR_raw: {df['KCOR'].equals(df['KCOR_raw'])}")
        
        # Check for any differences
        diff = df['KCOR'] - df['KCOR_raw']
        print(f"Max absolute difference: {np.abs(diff).max()}")
        print(f"Any non-zero differences: {np.any(diff != 0)}")
        
        # Show first few rows with all columns
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        # Check data types
        print(f"\nData types:")
        print(df.dtypes)
        
        # Check for any NaN values
        print(f"\nNaN counts:")
        print(df.isna().sum())
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
