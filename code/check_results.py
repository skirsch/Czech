#!/usr/bin/env python3
"""
Quick script to check if KCOR and KCOR_raw are now properly diverging
"""

import pandas as pd
import numpy as np

def main():
    # Read the output file
    try:
        df = pd.read_excel('../analysis/KCOR_analysis.xlsx', sheet_name='2021_24_BY1940_D2v0_KCOR')
        print(f"Successfully read {len(df)} rows from KCOR_analysis.xlsx")
        
        # Check if we have both KCOR and KCOR_raw columns
        if 'KCOR' in df.columns and 'KCOR_raw' in df.columns:
            print("\nColumns found:")
            print(f"KCOR: {df['KCOR'].notna().sum()} non-null values")
            print(f"KCOR_raw: {df['KCOR_raw'].notna().sum()} non-null values")
            
            # Compare the curves
            print("\nComparing KCOR vs KCOR_raw:")
            
            # Check if they're different
            if not df['KCOR'].equals(df['KCOR_raw']):
                print("✅ SUCCESS: KCOR and KCOR_raw are different!")
                
                # Show ranges
                print(f"\nKCOR range: {df['KCOR'].min():.6f} to {df['KCOR'].max():.6f}")
                print(f"KCOR_raw range: {df['KCOR_raw'].min():.6f} to {df['KCOR_raw'].max():.6f}")
                
                # Show first few rows
                print("\nFirst 5 rows:")
                print(df[['KCOR', 'KCOR_raw']].head())
                
                # Show correlation
                correlation = df['KCOR'].corr(df['KCOR_raw'])
                print(f"\nCorrelation between KCOR and KCOR_raw: {correlation:.6f}")
                
                # Show differences
                diff = df['KCOR'] - df['KCOR_raw']
                print(f"Max absolute difference: {np.abs(diff).max():.6f}")
                print(f"Mean absolute difference: {np.abs(diff).mean():.6f}")
                
            else:
                print("❌ FAILURE: KCOR and KCOR_raw are still identical!")
        else:
            print("❌ Missing required columns!")
            print(f"Available columns: {list(df.columns)}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
