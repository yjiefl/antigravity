import pandas as pd
file_path = '/Users/yangjie/code/antigravity/运营日报表审核/2026年02月10日运营日报表.xlsx'
df = pd.read_excel(file_path, header=None)

print("Row 3 full columns:")
for i, val in enumerate(df.iloc[3]):
    print(f"Col {i}: {val}")

print("\nRow 6 full columns:")
for i, val in enumerate(df.iloc[6]):
    print(f"Col {i}: {val}")

print("\nRow 9 full columns:")
for i, val in enumerate(df.iloc[9]):
    print(f"Col {i}: {val}")
