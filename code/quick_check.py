#!/usr/bin/env python3
"""
Quick check to see if disabling scaling fixed the issue
"""

import pandas as pd
import numpy as np
from pathlib import Path

def quick_check():
    # Read the KCOR analysis file
    file_path = Path("../analysis/KCOR_analysis.xlsx")
    
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
    
    # Get sheet names
    xls = pd.ExcelFile(file_path)
    kcor_sheets = [sheet for sheet in xls.sheet_names if "KCOR" in sheet]
    
    if not kcor_sheets:
        print("No KCOR sheets found!")
        return
    
    # Read the first KCOR sheet
    sheet_name = kcor_sheets[0]
    print(f"Analyzing sheet: {sheet_name}")
    
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    
    # Check if we have the expected columns
    if 'KCOR' not in df.columns or 'KCOR_raw' not in df.columns:
        print("Missing expected columns KCOR or KCOR_raw")
        return
    
    # Quick comparison
    print(f"\n=== Quick KCOR vs KCOR_raw Check ===")
    print(f"KCOR mean: {df['KCOR'].mean():.6f}")
    print(f"KCOR_raw mean: {df['KCOR_raw'].mean():.6f}")
    print(f"Correlation: {df['KCOR'].corr(df['KCOR_raw']):.6f}")
    print(f"Mean absolute difference: {(df['KCOR'] - df['KCOR_raw']).abs().mean():.10f}")
    
    # Check first few values
    print(f"\nFirst 5 values:")
    for i in range(min(5, len(df))):
        row = df.iloc[i]
        print(f"  {i}: KCOR={row['KCOR']:.6f}, KCOR_raw={row['KCOR_raw']:.6f}, Diff={row['KCOR'] - row['KCOR_raw']:.10f}")
    
    # Check if they're still identical
    if df['KCOR'].equals(df['KCOR_raw']):
        print("\n❌ Still identical!")
    else:
        print("\n✅ Now different!")

if __name__ == "__main__":
    quick_check()
