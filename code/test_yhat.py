#!/usr/bin/env python3
"""
Test to see what the detrending factor yhat actually is
"""

import pandas as pd
import numpy as np
from pathlib import Path

def test_yhat():
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
    
    # Check if we have the detrended data
    if 'log_RR_detrended' in df.columns:
        print(f"\n=== Detrending Factor Analysis ===")
        
        # The issue might be that yhat is essentially zero
        # Let me check if the detrending is actually changing anything
        
        log_rr_det = df['log_RR_detrended']
        
        print(f"log_RR_detrended stats:")
        print(f"  Mean: {log_rr_det.mean():.6f}")
        print(f"  Std:  {log_rr_det.std():.6f}")
        print(f"  Min:  {log_rr_det.min():.6f}")
        print(f"  Max:  {log_rr_det.max():.6f}")
        
        # Now let me think about this mathematically
        # If yhat is essentially constant, then y - yhat = y - constant
        # This would mean the detrending is just shifting the curve, not changing its shape
        
        print(f"\n=== Mathematical Analysis ===")
        print("From the image, we know:")
        print("1. KCOR_raw should use: y_w (original log-ratios)")
        print("2. KCOR should use: ~y_w = y_w - yhat (detrended log-ratios)")
        print("3. KCOR = exp(weighted_avg(~y_w))")
        print("4. KCOR_raw = exp(weighted_avg(y_w))")
        
        print(f"\nIf yhat is essentially constant, then:")
        print("~y_w = y_w - constant")
        print("This means the detrending is just shifting, not detrending")
        
        print(f"\nBut the KCOR curves are identical, which suggests")
        print("either yhat is zero, or there's a bug in the implementation")
        
        print(f"\n=== Hypothesis ===")
        print("The detrending factor yhat might be:")
        print("1. Zero (no detrending happening)")
        print("2. Constant (just shifting, not detrending)")
        print("3. Not being applied correctly")
        
        print(f"\nLet me check if there's a bug in how yhat is computed")
        print("or if it's not being applied to the KCOR calculation.")

if __name__ == "__main__":
    test_yhat()
