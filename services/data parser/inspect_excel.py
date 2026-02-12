import pandas as pd
import sys

file_path = '/Users/yangjie/code/antigravity/services/data parser/input/中能建广西公司_运营日报20260210_2026-02-11.xlsx'

try:
    # Load the excel file
    xls = pd.ExcelFile(file_path)
    print(f"Sheet names: {xls.sheet_names}")
    
    # Read the first sheet (usually the daily report)
    df = pd.read_excel(file_path, header=None)
    
    print("\nRows 15-25 (Raw):")
    for i, row in df.iloc[15:25].iterrows():
        print(f"Row {i}: {row.tolist()}")

except Exception as e:
    print(f"Error: {e}")
