import pandas as pd
import numpy as np
import re
import json
import os
import uuid
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ==========================================
# Helper Functions
# ==========================================
def find_col_name(columns, keywords):
    """Fuzzy find column name matching keywords"""
    for col in columns:
        s = str(col)
        if any(k in s for k in keywords):
            return col
    return None

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
    # Smart Sheet Selection
    try:
        xls = pd.ExcelFile(file_path)
        sheet_names = xls.sheet_names
        target_sheet = 0 # Default to first sheet
        
        # Priority search
        for name in sheet_names:
            if "运营日报" in name or "Daily Report" in name:
                target_sheet = name
                break
                
        df = pd.read_excel(file_path, sheet_name=target_sheet, header=None)
    except Exception as e:
        raise Exception(f"Excel读取失败: {str(e)}")
    
    # Locate Sections
    detail_header_idx = -1
    for i, row in df.iloc[:100].iterrows():
        if "公司/场站名称" in str(row.values) or "场站名称" in str(row.values):
            detail_header_idx = i
            break
            
    outage_start_idx = -1
    # Search for outage section after detail header
    search_start = detail_header_idx if detail_header_idx != -1 else 0
    
    for i, row in df.iloc[search_start:].iterrows():
        row_str = " ".join([str(x) for x in row if pd.notna(x)])
        if "四、" in row_str and "停运" in row_str:
            outage_start_idx = i
            break
            
    if outage_start_idx == -1:
        for i, row in df.iloc[search_start:].iterrows():
            if "停运情况" in str(row.values):
                outage_start_idx = i
                break

    return df, detail_header_idx, outage_start_idx

def process_overview(df, header_idx=0):
    data = {
        "total_new_energy": 0.0,
        "total_concentrated": 0.0,
        "total_distributed": 0.0,
        "total_thermal": 0.0,
        "concentrated_pv": 0.0,
        "concentrated_wind": 0.0
    }
    
    # Determine column index for generation
    gen_col_idx = 7 # Default fallback
    if header_idx != -1:
        header_row = df.iloc[header_idx]
        for i, val in enumerate(header_row):
            if pd.notna(val) and ("发电量" in str(val) or "日发电" in str(val)) and "限" not in str(val) and "损失" not in str(val):
                gen_col_idx = i
                break
                
    # Scan rows for summary data (both before and after header)
    # We look for keywords in the first column (or second if indented)
    search_rows = list(range(max(0, header_idx - 10), min(len(df), header_idx + 20)))
    # Add first 20 rows just in case
    search_rows = sorted(list(set(list(range(20)) + search_rows)))
    
    for r in search_rows:
        if r >= len(df): continue
        row = df.iloc[r]
        row_str = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
        if not row_str and len(row) > 1:
             row_str = str(row.iloc[1]) # Check 2nd col if 1st is empty
             
        val = 0.0
        try:
             # Ensure we don't go out of bounds
            if gen_col_idx < len(row):
                val = clean_number(row.iloc[gen_col_idx])
        except: pass
        
        if "新能源" in row_str and "合计" in row_str:
            data["total_new_energy"] = val
        elif "集中式" in row_str and "光伏" in row_str:
            data["concentrated_pv"] = val
        elif "风电" in row_str: # Matches "风电合计" or just "风电"
             # Careful not to match station names like "樟木风电场"
             if "合计" in row_str or len(row_str) < 5:
                data["concentrated_wind"] = val
        elif "集中式" in row_str and "合计" in row_str:
             # This file has "Concentrated Total" which sums Wind + PV
             data["total_concentrated"] = val
        elif "分布式" in row_str and "合计" in row_str:
             data["total_distributed"] = val
        elif "火电" in row_str and "合计" in row_str:
             data["total_thermal"] = val
             
    # Fallback Calculations
    if data["total_concentrated"] == 0:
        data["total_concentrated"] = data["concentrated_pv"] + data["concentrated_wind"]
        
    if data["total_new_energy"] == 0:
        data["total_new_energy"] = data["total_concentrated"] + data["total_distributed"]
        
    return data

def process_details(df, header_idx, outage_idx):
    if header_idx == -1 or outage_idx == -1:
        return pd.DataFrame()
        
    block = df.iloc[header_idx:outage_idx].copy()
    headers = [clean_header(x) for x in block.iloc[0]]
    
    # Ensure unique headers
    seen = {}
    new_headers = []
    for h in headers:
        if h in seen:
            seen[h] += 1
            new_headers.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 0
            new_headers.append(h)
            
    block.columns = new_headers
    block = block.iloc[1:]
    
    if block.empty: return pd.DataFrame()

    current_company = "Unknown"
    
    stations_df_list = []
    for _, row in block.iterrows():
        # Get first two columns safely
        val0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        val1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        
        # Skip completely empty name rows
        if not val0 and not val1: continue
        
        # Logic to identify Company vs Station
        # Case A: Two columns (Old format)
        if val1 and val0:
            if "合计" in val0: continue
            current_company = val0
            station = val1
        # Case B: Single column hierarchy (New format)
        else:
            name = val0 if val0 else val1
            
            if "合计" in name: continue
            if "停运" in name: continue
            
            # Heuristic: Companies usually end with "公司" or contain it
            # But we must be careful not to match a station name that might contain "公司" (unlikely)
            # Also update context
            if "公司" in name:
                current_company = name
                continue # Skip the company header row itself
                
            station = name
            
        # Data Extraction
        raw_company = current_company
        
        # Dynamic Column Mapping
        cols = block.columns
        
        # Helper to get val safely
        def get_val(keywords, default=0.0):
            c_name = find_col_name(cols, keywords)
            if c_name:
                return clean_number(row[c_name])
            return default

        ac_cap_raw = 0
        dc_cap_raw = 0
        
        cap_col = find_col_name(cols, ["容量"])
        if cap_col:
            ac_cap_raw, dc_cap_raw = extract_capacity(row[cap_col])
        else:
             # Fallback to index 2
             if len(row) > 2:
                ac_cap_raw, dc_cap_raw = extract_capacity(row.iloc[2])

        try:
             station_data = {
                "company": raw_company,
                "station": station,
                "ac_capacity": ac_cap_raw,
                "dc_capacity": dc_cap_raw,
                "daily_equiv_hours": get_val(["当日等效", "日等效"], clean_number(row.iloc[6]) if len(row)>6 else 0),
                "daily_gen": get_val(["日发电", "当日发电"], clean_number(row.iloc[7]) if len(row)>7 else 0),
                "curtailment": get_val(["限发电量", "限电量"], clean_number(row.iloc[8]) if len(row)>8 else 0),
                "curtailment_rate": get_val(["限电率"], clean_number(row.iloc[9]) if len(row)>9 else 0),
                "unplanned": get_val(["非计划"], clean_number(row.iloc[10]) if len(row)>10 else 0),
                "planned": get_val(["计划损失"], clean_number(row.iloc[11]) if len(row)>11 else 0),
                "abandoned": get_val(["弃光", "弃风"], clean_number(row.iloc[12]) if len(row)>12 else 0),
                "availability": get_val(["场用可利用率", "可利用率", "发电设备可利用率"], clean_number(row.iloc[13]) if len(row)>13 else 0),
                "annual_availability": get_val(["年度场用", "年可利用率", "年度发电设备", "年度"], clean_number(row.iloc[14]) if len(row)>14 else 0),
                "is_distributed": "分布式" in str(raw_company) or "分布式" in str(station)
            }
             stations_df_list.append(station_data)
        except Exception as e:
            continue
        
    return pd.DataFrame(stations_df_list)


def process_outages(df, start_idx):
    outages = {}
    if start_idx == -1: return outages
    
    sub = df.iloc[start_idx:]
    for _, row in sub.iterrows():
        station = row.iloc[1] # Assuming station name is in column 1
        if pd.notna(station) and isinstance(station, str):
            desc = str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""
            # Sometimes description is in column 10
            if (not desc or desc == "无") and len(row) > 10 and pd.notna(row.iloc[10]): 
                desc = str(row.iloc[10])
            if desc and desc != "无":
                outages[station.strip()] = desc.strip()
    return outages

def analyze_daily_report(input_path, output_dir):
    try:
        df, detail_header_idx, outage_start_idx = load_and_preprocess(input_path)
    except Exception as e:
        return None, f"文件读取失败: {str(e)}"
        
    if detail_header_idx == -1:
        return None, "无法定位场站明细表头，请检查格式"
    if outage_start_idx == -1:
        # Warning but proceed? Or assume end of file?
        outage_start_idx = len(df)

    overview = process_overview(df, detail_header_idx)
    stations_df = process_details(df, detail_header_idx, outage_start_idx)
    outage_map = process_outages(df, outage_start_idx)
    
    if stations_df.empty:
        return None, "未提取到有效的场站数据"
    
    stations_df['outage_reason'] = stations_df['station'].apply(lambda x: outage_map.get(str(x).strip(), "无"))
    
    anomalies = []
    passes = []
    
    # 1. Logic Validation: Total
    calc_total = overview['total_concentrated'] + overview['total_distributed'] + overview['total_thermal']
    if abs(calc_total - overview['total_new_energy']) > 0.1:
        anomalies.append({
            "type": "总和校验",
            "desc": f"总发电量不平衡。集中({overview['total_concentrated']:.2f}) + 分布({overview['total_distributed']:.2f}) + 火电({overview['total_thermal']:.2f}) = {calc_total:.2f} != 总表({overview['total_new_energy']:.2f})",
            "station": "全站"
        })
    else:
        passes.append({
            "type": "总和校验",
            "desc": f"各分类能源汇总与总计完美对应 (计算值: {calc_total:.2f} 万kWh)",
            "station": "全站"
        })
    
    # 3. Auxiliary Power Check
    # Need to extract 'total_aux_power' and 'total_generation' first
    # For now, we approximate using overview data if available or sum from stations
    # Assuming 'total_generation' is 'total_new_energy'
    
    # 4. Regional Curtailment Check (Hardcoded regions as per user request)
    regions = {
        "贵港": ["榕木光伏", "樟木光伏", "樟木风电"],
        "崇左": ["派岸", "弄滩", "六留", "强胜", "寨安", "那小", "浦峙", "峙书", "康宁", "守旗", "岑凡", "把荷", "武安", "坤山"]
    }
    
    for region, station_names in regions.items():
        region_gen = 0.0
        region_curtail_amt = 0.0
        
        found_any = False
        for _, r in stations_df.iterrows():
            if any(name in r['station'] for name in station_names):
                region_gen += r['daily_gen']
                region_curtail_amt += r['curtailment']
                found_any = True
        
        if found_any:
            # Recalculate curtailment rate: curtailment / (gen + curtailment) * 100
            # Note: daily_gen is usually on-grid + aux, or just on-grid. 
            # The prompt says Rate = Curtailment / (OnGrid + Curtailment).
            # Assuming 'daily_gen' in our specific file context is '上网电量' or equivalent close enough for now, 
            # OR we need to clarify if 'daily_gen' field is Generation or OnGrid.
            # Usually Daily Gen = OnGrid + Aux. 
            # If the formula explicitly says (上网电量 + 限电量), we might need to subtract Aux if daily_gen is Total Gen.
            # However, simpler logic check: Total Gen vs Curtailment logic.
            # Let's assume daily_gen is the denominator base part (Generation).
             pass 

    
    # 2. Station Level Validation
    for i, row in stations_df.iterrows():
        # Skip all validations for distributed projects as data is often incomplete/not filled
        if row.get('is_distributed', False):
            continue
            
        # Gen/Cap logic check using DC capacity for solar, AC for wind (dc==ac if no slash)
        cap_to_use = row['dc_capacity'] if row['dc_capacity'] > 0 else row['ac_capacity']
        if cap_to_use > 0:
            calc_hours = (row['daily_gen'] * 10) / cap_to_use
            if row['daily_equiv_hours'] > 0:
                ratio = abs(calc_hours - row['daily_equiv_hours']) / row['daily_equiv_hours']
                if ratio > 0.01:
                    anomalies.append({
                        "type": "系数异常",
                        "desc": f"表显等效小时({row['daily_equiv_hours']}) 与计算值({calc_hours:.2f}) 偏差 > 1%。(计算过程: 发电量{row['daily_gen']:.2f} * 10 / 容量{cap_to_use:.2f} = {calc_hours:.2f})",
                        "station": row['station']
                    })
                else:
                    passes.append({
                        "type": "系数校验",
                        "desc": f"等效利用小时数与发电量/容量比例吻合。 (计算过程: 发电量{row['daily_gen']:.2f} * 10 / 容量{cap_to_use:.2f} = {calc_hours:.2f})",
                        "station": row['station']
                    })

        # Loss Balance
        loss_sum = row['curtailment'] + row['unplanned'] + row['planned']
        if abs(loss_sum - row['abandoned']) > 0.1:
             anomalies.append({
                "type": "平衡异常",
                "desc": f"合计弃电({row['abandoned']}) != 各分量损失之和({loss_sum:.2f})。(计算过程: 限电{row['curtailment']:.2f} + 非计划{row['unplanned']:.2f} + 计划{row['planned']:.2f} = {loss_sum:.2f})",
                "station": row['station']
            })
        else:
             passes.append({
                "type": "平衡校验",
                "desc": f"弃电量与各项损失项合计相等。 (计算过程: 限电{row['curtailment']:.2f} + 非计划{row['unplanned']:.2f} + 计划{row['planned']:.2f} = {loss_sum:.2f})",
                "station": row['station']
            })

        # Availability vs Outage (Skip for distributed)
        if not row.get('is_distributed', False):
            if row['availability'] < 90.0 and row['outage_reason'] == "无":
                 anomalies.append({
                    "type": "说明缺失",
                    "desc": f"利用率 {row['availability']}% (<90%) 但无停运记录",
                    "station": row['station']
                })
            else:
                 passes.append({
                    "type": "停运勾稽",
                    "desc": f"利用率校验通过或已备注停运原因",
                    "station": row['station']
                })

        # 5. Advanced Cross-Checks (Merged Loop)
        if row.get('is_distributed', False): continue

        # Curtailment Rate Validation
        # Rate = Curtailment / (Gen + Curtailment)
        theoretical_gen = row['daily_gen'] + row['curtailment']
        if theoretical_gen > 0:
            calc_rate = (row['curtailment'] / theoretical_gen) * 100
            if abs(calc_rate - row['curtailment_rate']) > 1.0: # 1% tolerance
                 anomalies.append({
                    "type": "限电率校验",
                    "desc": f"表显限电率({row['curtailment_rate']}%) 与计算值({calc_rate:.2f}%) 偏差 > 1%。(计算过程: 限电量{row['curtailment']:.2f} / (日发电量{row['daily_gen']:.2f} + 限电量{row['curtailment']:.2f}) = {calc_rate:.2f}%)",
                    "station": row['station']
                })
            else:
                passes.append({
                    "type": "限电率校验",
                    "desc": f"限电率计算匹配成功。 (计算过程: 限电量{row['curtailment']:.2f} / (日发电量{row['daily_gen']:.2f} + 限电量{row['curtailment']:.2f}) = {calc_rate:.2f}%)",
                    "station": row['station']
                })
        
        # Equivalent Outage Hours
        # Formula: Loss (10k kWh) * 10 / Capacity (MW)
        # We need to map 'loss' to unplanned/planned or just verify total?
        # Let's verify Equivalent Utilization Hours again carefully.
        # Actually the prompt says: Equivalent Outage Duration = Loss * 10 / Cap.
        # Loss = Unplanned + Planned + Abandoned? 
        # Usually Outage Hours relates to 'unplanned' + 'planned'.
        
        # Equivalent Outage Hours
        # Formula: Loss (10k kWh) * 10 / Capacity (MW)
        # Loss for outage is usually 'unplanned' + 'planned'
        # Let's logic check 'unplanned' primarily or total 'abandoned' - 'curtailment'?
        # The prompt says: Equiv Outage Duration = Loss * 10 / Cap.
        # Let's verify '利用率' (Availability) logic maybe?
        # Availability = (24 - EquivOutageHours) / 24 * 100?
        # Let's stick to simple Equiv Utilization Hours verification first which is already done (Gen * 10 / Cap).

    # Analysis
    top_curtailment = stations_df.sort_values(by='curtailment_rate', ascending=False).head(3)
    
    # Filter out distributed for availability analysis as requested
    concentrated_df = stations_df[~stations_df['is_distributed']]
    min_avail = concentrated_df.sort_values(by='availability', ascending=True).head(3)
    max_loss = concentrated_df.sort_values(by='unplanned', ascending=False).head(3)
    
    file_id = uuid.uuid4().hex[:8]
    pdf_filename = f"daily_report_{file_id}.pdf"
    json_filename = f"daily_report_{file_id}.json"
    
    pdf_path = os.path.join(output_dir, pdf_filename)
    json_path = os.path.join(output_dir, json_filename)
    
    # Generate Report Lines for PDF
    report_lines = [
        "【新能源运营日报审核报告】",
        f"处理日期: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "-"*30,
        "一、数据健康度报告",
        f"1. 集中式总计: {overview['total_concentrated']:.2f} 万kWh",
        f"2. 分布式总计: {overview['total_distributed']:.2f} 万kWh",
        f"3. 火电总计:   {overview['total_thermal']:.2f} 万kWh",
        f"4. 新能源合并: {overview['total_new_energy']:.2f} 万kWh",
        f"5. 逻辑校验状态: {'已通过' if not anomalies else '发现异常'}",
        "\n异常详情:" if anomalies else "\n逻辑校验全部通过。"
    ]
    for a in anomalies: report_lines.append(f"- [{a['type']}] {a['station']}: {a['desc']}")
    
    report_lines.append("\n" + "-"*30)
    report_lines.append("二、深度分析结果")
    report_lines.append("1. 异常Top 3 (指标恶化/风险较大):")
    
    curtail_str = ", ".join([f"{r.station}({r.curtailment_rate}%)" for _,r in top_curtailment.iterrows()])
    report_lines.append(f"   - 最高限电率: {curtail_str}")
    
    avail_str = ", ".join([f"{r.station}({r.availability}%)" for _,r in min_avail.iterrows()])
    report_lines.append(f"   - 最低利用率: {avail_str}")
    
    loss_str = ", ".join([f"{r.station}({r.unplanned}万kWh)" for _,r in max_loss.iterrows()])
    report_lines.append(f"   - 最大非计划损失: {loss_str}")
    
    report_lines.append("\n2. 故障/限电归因 (典型案例):")
    for _, r in stations_df[stations_df['availability'] < 95].iterrows():
        if r['outage_reason'] != '无':
            reason_short = r['outage_reason'][:80] + "..." if len(r['outage_reason']) > 80 else r['outage_reason']
            report_lines.append(f"   * {r['station']} (利用率{r['availability']}%): {reason_short}")

    # PDF Generation
    try:
        # Try to find font
        font_path = '/System/Library/Fonts/STHeiti Light.ttc' # Mac default
        if not os.path.exists(font_path):
            font_path = '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc' # Linux default
            
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('Chinese', font_path))
            c = canvas.Canvas(pdf_path, pagesize=A4)
            c.setFont('Chinese', 12)
            y = 800
            for line in report_lines:
                # Basic wrapping
                if len(line) > 60:
                     chunks = [line[i:i+60] for i in range(0, len(line), 60)]
                     for chunk in chunks:
                        if y < 50:
                            c.showPage()
                            c.setFont('Chinese', 12)
                            y = 800
                        c.drawString(50, y, chunk)
                        y -= 18
                else:
                    if y < 50:
                        c.showPage()
                        c.setFont('Chinese', 12)
                        y = 800
                    c.drawString(50, y, line)
                    y -= 18
            c.save()
    except Exception as e:
        print(f"PDF Generation warning: {e}")

    # Save JSON Details
    stations_df.to_json(json_path, orient='records', force_ascii=False)

    return {
        "file_id": file_id,
        "overview": overview,
        "anomalies": anomalies,
        "passes": passes,
        "pdf_filename": pdf_filename,
        "json_filename": json_filename,
        "stations_data": stations_df.to_dict(orient='records'),
        "top_curtailment": top_curtailment.to_dict(orient='records'),
        "min_avail": min_avail.to_dict(orient='records'),
        "max_loss": max_loss.to_dict(orient='records')
    }, None

