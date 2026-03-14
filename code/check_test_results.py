#!/usr/bin/env python3
"""
Check the test results to see if detrending is working correctly
"""

import pandas as pd
import numpy as np

def main():
    try:
        # Read the test analysis results
        df = pd.read_excel('../analysis/KCOR_test_analysis.xlsx', sheet_name='2020_01_BY1940_D2v0_KCOR')
        print(f"Successfully read {len(df)} rows from test analysis")
        
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
                
                # Check if KCOR is flat (detrending worked)
                kcor_std = df['KCOR'].std()
                kcor_raw_std = df['KCOR_raw'].std()
                
                print(f"\nKCOR standard deviation: {kcor_std:.6f}")
                print(f"KCOR_raw standard deviation: {kcor_raw_std:.6f}")
                
                if kcor_std < kcor_raw_std * 0.1:  # KCOR should be much flatter
                    print("✅ SUCCESS: KCOR is much flatter than KCOR_raw (detrending worked!)")
                else:
                    print("❌ FAILURE: KCOR is not significantly flatter than KCOR_raw")
                
                # Show first few rows
                print("\nFirst 5 rows:")
                print(df[['KCOR', 'KCOR_raw']].head())
                
                # Show correlation
                correlation = df['KCOR'].corr(df['KCOR_raw'])
                print(f"\nCorrelation between KCOR and KCOR_raw: {correlation:.6f}")
                
                # Check why correlation might be NaN
                if pd.isna(correlation):
                    print("⚠️  Correlation is NaN - investigating why:")
                    print(f"KCOR variance: {df['KCOR'].var():.10f}")
                    print(f"KCOR_raw variance: {df['KCOR_raw'].var():.10f}")
                    print(f"KCOR unique values: {df['KCOR'].nunique()}")
                    print(f"KCOR_raw unique values: {df['KCOR_raw'].nunique()}")
                    
                    if df['KCOR'].nunique() == 1:
                        print("✅ KCOR has only one unique value (perfectly flat) - this is expected!")
                        print("Correlation is undefined when one variable is constant.")
                    else:
                        print("❌ Unexpected: KCOR has multiple values but correlation is still NaN")
                
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
