import pandas as pd
import numpy as np
import re
import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==========================================
# Configuration & Constants
# ==========================================
POSSIBLE_PATHS = [
    '/Users/yangjie/code/antigravity/运营日报表审核/2026年02月10日运营日报表.xlsx',
    '/Users/yangjie/code/antigravity/运营日报表审核/input/2026年02月10日运营日报表.xlsx'
]
FILE_PATH = None
for p in POSSIBLE_PATHS:
    if os.path.exists(p):
        FILE_PATH = p
        break

if not FILE_PATH:
    dir_path = '/Users/yangjie/code/antigravity/运营日报表审核/'
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".xlsx") and "2026" in file:
                FILE_PATH = os.path.join(root, file)
                break
        if FILE_PATH: break

OUTPUT_JSON = '/Users/yangjie/code/antigravity/运营日报表审核/cleaned_data.json'
OUTPUT_REPORT_TXT = '/Users/yangjie/code/antigravity/运营日报表审核/analysis_report.txt'
OUTPUT_REPORT_PDF = '/Users/yangjie/code/antigravity/运营日报表审核/analysis_report.pdf'
FONT_PATH = '/Library/Fonts/Arial Unicode.ttf'

# ==========================================
# Helper Functions
# ==========================================
def clean_header(val):
    if pd.isna(val): return str(val)
    return str(val).replace('\n', '').strip()

def extract_capacity(val):
    """
    Specially handle capacity like '90MW/126MWp'
    Returns (AC, DC/Peak)
    """
    if pd.isna(val): return 0.0, 0.0
    s = str(val).replace(',', '')
    parts = s.split('/')
    
    def get_num(text):
        m = re.search(r'-?\d*\.?\d+', text)
        return float(m.group()) if m else 0.0
        
    ac = get_num(parts[0])
    dc = get_num(parts[1]) if len(parts) > 1 else ac
    return ac, dc

def clean_number(val):
    if pd.isna(val): return 0.0
    s = str(val).replace(',', '').replace('%', '')
    match = re.search(r'-?\d*\.?\d+', s)
    return float(match.group()) if match else 0.0

def load_and_preprocess(file_path):
    df = pd.read_excel(file_path, header=None)
    
    # Locate Sections
    detail_header_idx = -1
    for i, row in df.iloc[:100].iterrows():
        if "公司/场站名称" in str(row.values):
            detail_header_idx = i
            break
            
    outage_start_idx = -1
    for i, row in df.iloc[detail_header_idx:].iterrows():
        row_str = " ".join([str(x) for x in row if pd.notna(x)])
        if "四、" in row_str and "停运" in row_str:
            outage_start_idx = i
            break
            
    if outage_start_idx == -1:
        for i, row in df.iloc[detail_header_idx:].iterrows():
            if "停运情况" in str(row.values):
                outage_start_idx = i
                break

    return df, detail_header_idx, outage_start_idx

def process_overview(df):
    data = {
        "total_new_energy": 0.0,
        "total_concentrated": 0.0,
        "total_distributed": 0.0,
        "total_thermal": 0.0,
        "concentrated_pv": 0.0,
        "concentrated_wind": 0.0
    }
    
    for r in range(20):
        row = df.iloc[r]
        row_list = [str(x) for x in row.values]
        
        if "新能源" in row_list:
            idx = row_list.index("新能源")
            data["total_new_energy"] = clean_number(row.iloc[idx+2])
        if "集中式光伏" in row_list:
            idx = row_list.index("集中式光伏")
            data["concentrated_pv"] = clean_number(row.iloc[idx+2])
        if "风电" in row_list:
            idx = row_list.index("风电")
            data["concentrated_wind"] = clean_number(row.iloc[idx+2])
        if "分布式光伏" in row_list:
            idx = row_list.index("分布式光伏")
            data["total_distributed"] = clean_number(row.iloc[idx+2])
        if "火电" in row_list:
            idx = row_list.index("火电")
            data["total_thermal"] = clean_number(row.iloc[idx+2])

    data["total_concentrated"] = data["concentrated_pv"] + data["concentrated_wind"]
    
    # Verify against subtotal row in detail table if needed
    # (Skip for now as Row 3 matches Row 26 sum)
    
    return data

def process_details(df, header_idx, outage_idx):
    block = df.iloc[header_idx:outage_idx].copy()
    headers = [clean_header(x) for x in block.iloc[0]]
    block.columns = headers
    block = block.iloc[1:]
    
    company_col = block.columns[0]
    block['Company_Fill'] = block[company_col].ffill()
    
    stations = []
    for _, row in block.iterrows():
        company = row['Company_Fill']
        station = row.iloc[1]
        raw_company = str(row.iloc[0])
        
        if "合计" in raw_company: continue
        if pd.isna(station): continue
            
        ac_cap, dc_cap = extract_capacity(row.iloc[2])
        
        station_data = {
            "company": company,
            "station": station,
            "ac_capacity": ac_cap,
            "dc_capacity": dc_cap,
            "daily_equiv_hours": clean_number(row.iloc[6]),
            "daily_gen": clean_number(row.iloc[7]),
            "curtailment": clean_number(row.iloc[8]),
            "curtailment_rate": clean_number(row.iloc[9]),
            "unplanned": clean_number(row.iloc[10]),
            "planned": clean_number(row.iloc[11]),
            "abandoned": clean_number(row.iloc[12]),
            "availability": clean_number(row.iloc[13]),
            "annual_availability": clean_number(row.iloc[14])
        }
        stations.append(station_data)
        
    return pd.DataFrame(stations)

def process_outages(df, start_idx):
    outages = {}
    sub = df.iloc[start_idx:]
    for _, row in sub.iterrows():
        station = row[1]
        if pd.notna(station) and isinstance(station, str):
            desc = str(row[4]) if pd.notna(row[4]) else ""
            if (not desc or desc == "无") and pd.notna(row[10]): desc = str(row[10])
            if desc and desc != "无":
                outages[station.strip()] = desc.strip()
    return outages

def main():
    if not FILE_PATH:
        print("Error: Excel file not found.")
        return

    df, detail_header_idx, outage_start_idx = load_and_preprocess(FILE_PATH)
    overview = process_overview(df)
    stations_df = process_details(df, detail_header_idx, outage_start_idx)
    outage_map = process_outages(df, outage_start_idx)
    
    stations_df['outage_reason'] = stations_df['station'].apply(lambda x: outage_map.get(x.strip(), "无"))
    
    anomalies = []
    
    # 1. Logic Validation: Total
    calc_total = overview['total_concentrated'] + overview['total_distributed'] + overview['total_thermal']
    if abs(calc_total - overview['total_new_energy']) > 0.1:
        anomalies.append(f"总和校验失败: 集中({overview['total_concentrated']:.2f}) + 分布({overview['total_distributed']:.2f}) + 火电({overview['total_thermal']:.2f}) != 总({overview['total_new_energy']:.2f})")
    
    # 2. Station Level Validation
    for i, row in stations_df.iterrows():
        # Gen/Cap check using DC capacity for solar, AC for wind (dc==ac if no slash)
        cap_to_use = row['dc_capacity'] if row['dc_capacity'] > 0 else row['ac_capacity']
        if cap_to_use > 0:
            calc_hours = (row['daily_gen'] * 10) / cap_to_use
            if row['daily_equiv_hours'] > 0:
                ratio = abs(calc_hours - row['daily_equiv_hours']) / row['daily_equiv_hours']
                if ratio > 0.01:
                    anomalies.append(f"系数异常: {row['station']} 记录小时({row['daily_equiv_hours']}) vs 计算小时({calc_hours:.2f}, 基于{cap_to_use}MW) 偏差 > 1%")

        # Loss Balance
        loss_sum = row['curtailment'] + row['unplanned'] + row['planned']
        if abs(loss_sum - row['abandoned']) > 0.1:
            anomalies.append(f"平衡异常: {row['station']} 弃电({row['abandoned']}) != 损失项和({loss_sum:.2f})")

        # Availability vs Outage
        if row['availability'] < 90.0 and row['outage_reason'] == "无":
            anomalies.append(f"说明缺失: {row['station']} 利用率 {row['availability']}% (<90%) 但无停运记录")

    # Analysis
    top_curtailment = stations_df.sort_values(by='curtailment_rate', ascending=False).head(3)
    min_avail = stations_df.sort_values(by='availability', ascending=True).head(3)
    max_loss = stations_df.sort_values(by='unplanned', ascending=False).head(3)

    report_lines = [
        "【新能源运营日报审核报告】",
        f"处理日期: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"分析文件: {os.path.basename(FILE_PATH)}",
        "-"*30,
        "一、数据健康度报告",
        f"1. 集中式总计: {overview['total_concentrated']:.2f} 万kWh",
        f"2. 分布式总计: {overview['total_distributed']:.2f} 万kWh",
        f"3. 火电总计:   {overview['total_thermal']:.2f} 万kWh",
        f"4. 新能源合并: {overview['total_new_energy']:.2f} 万kWh",
        f"5. 逻辑校验状态: {'已通过' if not anomalies else '发现异常'}",
        "\n异常详情:" if anomalies else "\n逻辑校验全部通过。"
    ]
    for a in anomalies: report_lines.append(f"- {a}")

    report_lines.append("\n" + "-"*30)
    report_lines.append("二、深度分析结果")
    report_lines.append("1. 异常Top 3 (指标恶化/风险较大):")
    report_lines.append(f"   - 最高限电率: {', '.join([f'{r.station}({r.curtailment_rate}%)' for _,r in top_curtailment.iterrows()])}")
    report_lines.append(f"   - 最低利用率: {', '.join([f'{r.station}({r.availability}%)' for _,r in min_avail.iterrows()])}")
    report_lines.append(f"   - 最大非计划损失: {', '.join([f'{r.station}({r.unplanned}万kWh)' for _,r in max_loss.iterrows()])}")
    
    report_lines.append("\n2. 故障/限电归因 (典型案例):")
    for _, r in stations_df[stations_df['availability'] < 95].iterrows():
        if r['outage_reason'] != '无':
            report_lines.append(f"   * {r['station']} (利用率{r['availability']}%): {r['outage_reason'][:100]}...")

    # Save outputs
    with open(OUTPUT_REPORT_TXT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    # PDF Generation
    if os.path.exists(FONT_PATH):
        try:
            pdfmetrics.registerFont(TTFont('ArialUnicode', FONT_PATH))
            c = canvas.Canvas(OUTPUT_REPORT_PDF, pagesize=A4)
            c.setFont('ArialUnicode', 12)
            y = 800
            for line in report_lines:
                if y < 50:
                    c.showPage()
                    c.setFont('ArialUnicode', 12)
                    y = 800
                c.drawString(50, y, line)
                y -= 18
            c.save()
            print("PDF Report generated.")
        except Exception as e:
            print(f"PDF generation failed: {e}")

    stations_df.to_json(OUTPUT_JSON, orient='records', force_ascii=False, indent=2)
    print("All tasks completed.")

if __name__ == "__main__":
    main()
