#!/usr/bin/env python3
"""
Debug script to examine KCOR values before and after scaling
"""

import pandas as pd
import numpy as np

def main():
    try:
        df = pd.read_excel('../analysis/KCOR_analysis.xlsx', sheet_name='2021_24_BY1940_D2v0_KCOR')
        print(f"DataFrame shape: {df.shape}")
        
        # Check if we have the intermediate columns
        print("\nAvailable columns:")
        print(df.columns.tolist())
        
        # Look for any columns that might show pre-scaling values
        if 'log_RR_detrended' in df.columns:
            print("\nlog_RR_detrended analysis:")
            print(f"Range: {df['log_RR_detrended'].min():.6f} to {df['log_RR_detrended'].max():.6f}")
            print(f"First 5 values: {df['log_RR_detrended'].head().values}")
        
        # Check if we have weight information
        if 'weight' in df.columns:
            print(f"\nWeight analysis:")
            print(f"Range: {df['weight'].min():.2f} to {df['weight'].max():.2f}")
            print(f"Non-zero weights: {(df['weight'] > 0).sum()}")
        
        # Check the actual KCOR values
        print(f"\nKCOR analysis:")
        print(f"KCOR first 10 values: {df['KCOR'].head(10).values}")
        print(f"KCOR_raw first 10 values: {df['KCOR_raw'].head(10).values}")
        
        # Check if they're exactly equal
        print(f"\nKCOR equals KCOR_raw: {df['KCOR'].equals(df['KCOR_raw'])}")
        
        # Look for any differences
        diff = df['KCOR'] - df['KCOR_raw']
        print(f"Max absolute difference: {np.abs(diff).max()}")
        print(f"Any non-zero differences: {np.any(diff != 0)}")
        
        # Check if the issue is that both are scaled to 1.0 at the same point
        print(f"\nScaling analysis:")
        # Look for values close to 1.0
        kcor_ones = np.where(np.abs(df['KCOR'] - 1.0) < 1e-6)[0]
        kcor_raw_ones = np.where(np.abs(df['KCOR_raw'] - 1.0) < 1e-6)[0]
        print(f"KCOR values close to 1.0 at indices: {kcor_ones}")
        print(f"KCOR_raw values close to 1.0 at indices: {kcor_raw_ones}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
