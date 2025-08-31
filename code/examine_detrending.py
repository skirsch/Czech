#!/usr/bin/env python3
"""
Examine the detrending factor and understand why KCOR and KCOR_raw are practically identical
"""

import pandas as pd
import numpy as np

def main():
    try:
        df = pd.read_excel('../analysis/KCOR_analysis.xlsx', sheet_name='2021_24_BY1940_D2v0_KCOR')
        print(f"DataFrame shape: {df.shape}")
        
        # Show the key columns
        print("\nKey columns:")
        print(df[['KCOR', 'KCOR_raw', 'log_RR_detrended', 'RR_detrended']].head(10))
        
        # Check if we have the raw log rate ratios
        if 'log_RR_detrended' in df.columns:
            print(f"\nlog_RR_detrended range: {df['log_RR_detrended'].min():.6f} to {df['log_RR_detrended'].max():.6f}")
            
            # Try to reconstruct what the raw log rate ratios should be
            # If log_RR_detrended = y - yhat, then y = log_RR_detrended + yhat
            # But we need to know what yhat is
            
            # Let's look at the differences between KCOR and KCOR_raw more carefully
            print(f"\nDetailed comparison:")
            print(f"KCOR first 5 values: {df['KCOR'].head().values}")
            print(f"KCOR_raw first 5 values: {df['KCOR_raw'].head().values}")
            
            # Check if the issue is in the scaling
            print(f"\nScaling analysis:")
            print(f"KCOR / KCOR_raw ratio (first 5): {(df['KCOR'] / df['KCOR_raw']).head().values}")
            
            # Look for any non-unity ratios
            ratios = df['KCOR'] / df['KCOR_raw']
            non_unity = ratios[abs(ratios - 1.0) > 1e-10]
            print(f"Non-unity ratios found: {len(non_unity)}")
            if len(non_unity) > 0:
                print(f"Sample non-unity ratios: {non_unity.head().values}")
        
        # Check the weight column to see if it's being used correctly
        print(f"\nWeight analysis:")
        print(f"Weight range: {df['weight'].min():.2f} to {df['weight'].max():.2f}")
        print(f"Weight first 5: {df['weight'].head().values}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
