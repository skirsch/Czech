#!/usr/bin/env python3
"""
Check what sheets are available in the output file
"""

import pandas as pd

def main():
    try:
        # Read the Excel file to see available sheets
        xl_file = pd.ExcelFile('../analysis/KCOR_analysis.xlsx')
        print(f"Available sheets: {xl_file.sheet_names}")
        
        # Try to read the first sheet
        first_sheet = xl_file.sheet_names[0]
        print(f"\nReading first sheet: {first_sheet}")
        
        df = pd.read_excel('../analysis/KCOR_analysis.xlsx', sheet_name=first_sheet)
        print(f"Columns: {list(df.columns)}")
        print(f"Shape: {df.shape}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
