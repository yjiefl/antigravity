
import pandas as pd
import sys
import os

file_path = '/Users/yangjie/code/antigravity/services/data parser/input/运营日报 - 2026-02-11_2026-02-12.xls'

try:
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        sys.exit(1)

    # Load the excel file
    df = pd.read_excel(file_path, header=None)
    
    print("\nRows 25-60:")
    for i, row in df.iloc[25:60].iterrows():
        # Clean up row printing for readability, convert NaNs to ''
        clean_row = [str(x) if pd.notna(x) else '' for x in row]
        # Only print first few columns to avoid clutter
        print(f"Row {i}: {clean_row[:3]}") # Just Company, Station, Capacity

except Exception as e:
    print(f"Error: {e}")
