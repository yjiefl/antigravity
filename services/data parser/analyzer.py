import pandas as pd
import re
import os
import sys
from openpyxl import Workbook

# 目标场站列表
TARGET_STATIONS = [
    '守旗光伏电站', '岑凡光伏电站', '弄滩光伏电站', '强胜光伏电站', '派岸光伏电站', 
    '浦峙光伏电站', '峙书光伏电站', '康宁光伏电站', '寨安光伏电站', '坤山风电场', 
    '樟木光伏电站', '榕木光伏电站', '樟木风电场', '驮堪光伏电站', '把荷风电场', '武安风电场'
]

def parse_deduction_text(text):
    """
    解析扣分详情文本
    """
    if pd.isna(text) or not str(text).strip():
        return None
    
    text = str(text)
    # 正则规则
    item = re.search(r'考核条件:([^，,（\s]+)', text)
    score = re.search(r'得分:([\d.]+)', text)
    total_score = re.search(r'总分([\d.]+)', text)
    reason = re.search(r'原因：([^；;]+)', text)
    
    item_val = item.group(1).strip() if item else "未知考核项"
    score_val = float(score.group(1)) if score else 0.0
    total_val = float(total_score.group(1)) if total_score else 0.0
    deduction = round(total_val - score_val, 2)
    reason_val = reason.group(1).strip() if reason else "未知原因"
    
    return {
        '考核项': item_val,
        '扣分值': deduction,
        '原因': reason_val
    }

def analyze(input_file, output_file="分析结果.xlsx"):
    print(f"正在读取文件: {input_file}")
    df = pd.read_csv(input_file, encoding='utf-8')
    
    # 1. 过滤场站
    df = df[df['厂站名'].apply(lambda x: any(target in str(x) for target in TARGET_STATIONS))]
    if df.empty:
        print("未匹配到任何目标场站数据。")
        return
    
    # 2. 逆透视 (Unpivot)
    id_vars = ['厂站名', '日期', '统计类型']
    # 修正：列名格式为 "00:00扣分详情"，没有 "时刻" 字样
    value_vars = [c for c in df.columns if '扣分详情' in c]
    
    df_long = df.melt(id_vars=id_vars, value_vars=value_vars, var_name='时刻', value_name='扣分详情')
    df_long['时刻'] = df_long['时刻'].str.extract(r'(\d{2}:\d{2})')
    
    # 3. 过滤并解析
    df_long = df_long[df_long['扣分详情'].notna()]
    df_long['扣分详情'] = df_long['扣分详情'].astype(str)
    df_long = df_long[df_long['扣分详情'].str.strip() != ""]
    
    details = df_long['扣分详情'].apply(parse_deduction_text)
    df_long['考核项'] = details.apply(lambda x: x['考核项'] if x else None)
    df_long['扣分值'] = details.apply(lambda x: x['扣分值'] if x else 0.0)
    df_long['具体原因'] = details.apply(lambda x: x['原因'] if x else None)
    
    df_long = df_long[df_long['扣分值'] > 0]
    
    if df_long.empty:
        print("未发现实际扣分记录。")
        return

    # 4. 生成 Excel 报告
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        detail_sheet = df_long[['厂站名', '日期', '统计类型', '时刻', '考核项', '扣分值', '具体原因']]
        detail_sheet.to_excel(writer, index=False, sheet_name='明细表')
        
        summary_station = df_long.groupby('厂站名')['扣分值'].sum().reset_index().sort_values(by='扣分值', ascending=False)
        summary_station.to_excel(writer, index=False, sheet_name='汇总表', startrow=0, startcol=0)
        
        summary_item = df_long.groupby('考核项').size().reset_index(name='出现次数').sort_values(by='出现次数', ascending=False)
        summary_item.to_excel(writer, index=False, sheet_name='汇总表', startrow=0, startcol=4)

    # 5. 生成文字总结
    top_stations = summary_station.head(3)
    top_items = summary_item.head(3)
    
    print("\n--- 分析简报 ---")
    print(f"1. 扣分最严重的 3 个场站:")
    for i, row in top_stations.iterrows():
        print(f"   - {row['厂站名']}: 累计扣分 {row['扣分值']}")
        
    print(f"2. 最普遍的 3 类问题:")
    for i, row in top_items.iterrows():
        print(f"   - {row['考核项']}: 出现 {row['出现次数']} 次")
        
    print("3. 初步排查建议:")
    print("   - 针对测风塔/气象站数据上送问题，建议联系厂家检查通讯板卡和链路稳定性。")
    print("   - 针对可用功率测试不通过，建议核对算法逻辑与装机容量配置。")
    print(f"\nExcel 报告已生成: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <csv_file>")
    else:
        analyze(sys.argv[1])
