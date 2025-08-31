#!/usr/bin/env python3
"""
Check KCOR values to see if they're all identical
"""

import pandas as pd
import numpy as np

def main():
    try:
        # Read the KCOR analysis results
        df = pd.read_excel('../analysis/KCOR_analysis.xlsx', sheet_name='2021_24_BY1940_D2v0_KCOR')
        print(f"Successfully read {len(df)} rows from KCOR analysis")
        
        # Check KCOR values
        print(f"\nKCOR column:")
        print(f"  Unique values: {df['KCOR'].nunique()}")
        print(f"  Range: {df['KCOR'].min():.6f} to {df['KCOR'].max():.6f}")
        print(f"  Standard deviation: {df['KCOR'].std():.10f}")
        print(f"  First 10 values: {df['KCOR'].head(10).tolist()}")
        
        # Check KCOR_raw values
        print(f"\nKCOR_raw column:")
        print(f"  Unique values: {df['KCOR_raw'].nunique()}")
        print(f"  Range: {df['KCOR_raw'].min():.6f} to {df['KCOR_raw'].max():.6f}")
        print(f"  Standard deviation: {df['KCOR_raw'].std():.10f}")
        print(f"  First 10 values: {df['KCOR_raw'].head(10).tolist()}")
        
        # Check if KCOR is suspiciously flat
        if df['KCOR'].nunique() == 1:
            print("\n⚠️  WARNING: KCOR has only ONE unique value - this suggests a bug!")
        elif df['KCOR'].std() < 1e-6:
            print("\n⚠️  WARNING: KCOR standard deviation is extremely small - this suggests a bug!")
        else:
            print("\n✅ KCOR appears to have normal variation")
            
        # Check if KCOR_raw has reasonable variation
        if df['KCOR_raw'].nunique() == 1:
            print("⚠️  WARNING: KCOR_raw also has only ONE unique value - this suggests a deeper bug!")
        else:
            print("✅ KCOR_raw has normal variation")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
