import pandas as pd
file_path = '/Users/yangjie/code/antigravity/运营日报表审核/input/2026年02月10日运营日报表.xlsx'
df = pd.read_excel(file_path, header=None)
# Find 浦峙/北江光伏
for r in range(25, 60):
    val = str(df.iloc[r, 1])
    if "浦峙/北江" in val:
        print(f"Row {r} data:")
        print(f"  Col 1 (Name): {df.iloc[r, 1]}")
        print(f"  Col 2 (Cap): {df.iloc[r, 2]}")
        print(f"  Col 6 (Equiv): {df.iloc[r, 6]}")
        print(f"  Col 7 (Gen): {df.iloc[r, 7]}")
