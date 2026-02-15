import pandas as pd
import os
import re

# Standardize station names mapping
STATION_MAPPING = {
    '樟木': '樟木风电场',
    '把荷': '把荷风电场',
    '坤山': '坤山风电场',
    '武安': '武安风电场',
    '榕木': '榕木光伏电站', # Assuming based on pattern, though file says "樟木/榕木" usually together
    '守旗': '守旗光伏电站', # Need to verify exact mapping from files, but this is a start
    '岑凡': '岑凡光伏电站',
    '弄滩': '弄滩光伏电站',
    '强胜': '强胜光伏电站',
    '派岸': '派岸光伏电站',
    '浦峙': '浦峙光伏电站',
    '峙书': '峙书光伏电站',
    '康宁': '康宁光伏电站',
    '寨安': '寨安光伏电站',
    '驮堪': '驮堪光伏电站',
}

def normalize_station_name(name):
    """Normalize station name to full name using mapping or return as is if not found."""
    if not isinstance(name, str):
        return name
    name = name.strip()
    # Direct lookup
    if name in STATION_MAPPING:
        return STATION_MAPPING[name]
    # Reverse lookup (if full name is passed)
    if name in STATION_MAPPING.values():
        return name
    # Partial match (risky but useful)
    for k, v in STATION_MAPPING.items():
        if k in name:
            return v
    return name

def clean_numeric(val):
    """Clean numeric strings: remove commas, replace '-' with 0, convert to float."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s == '-' or s == '\\' or s == '':
        return 0.0
    s = s.replace(',', '').replace('¥', '')
    try:
        return float(s)
    except (ValueError, TypeError):
        return 0.0

def format_excel_date(val):
    """Convert Excel date serial numbers or other date formats to YYYY-MM."""
    if pd.isna(val) or val == '未知' or str(val).strip() == '' or str(val).lower() == 'nan':
        return '未知'
    
    # 1. Try numeric serial date (e.g., 45627)
    try:
        if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '', 1).isdigit()):
            num_val = float(val)
            if 30000 < num_val < 100000:
                dt = pd.to_datetime(num_val, unit='D', origin='1899-12-30')
                return dt.strftime('%Y-%m')
    except:
        pass

    # 2. Try Chinese format like "2025年1月" using Regex
    import re
    s_val = str(val).strip()
    match = re.search(r'(\d{4})[年/-](\d{1,2})', s_val)
    if match:
        year, month = match.groups()
        return f"{year}-{int(month):02d}"

    # 3. Try standard string parsing
    try:
        dt = pd.to_datetime(s_val)
        if 1900 < dt.year < 2100:
            return dt.strftime('%Y-%m')
    except:
        pass

    # Last resort fallback
    return s_val

def find_and_rename(df, keywords):
    """Find a column in df by keywords and return its original name."""
    cols = df.columns.tolist()
    # 1. Exact match
    for c in cols:
        if any(k == str(c).strip() for k in keywords):
            return c
    # 2. Contains match
    for c in cols:
        if any(k in str(c) for k in keywords):
            return c
    return None

def load_main_table(excel_file):
    """
    Load '数据表（两个细则系统）' handling multi-index headers.
    The sheet has complex headers. We'll read it without headers first to inspect.
    Actually, based on the `run_command` output:
    Row 0: NaN, 年月, 厂站, 免考情况, 检修管理总考核电量...
    Row 1: ...
    We need to identify columns by their names in row 0/1/2/3.
    """
    try:
        # Read with header=0 to get the first row as columns, but it's multi-level.
        # Let's read a few rows to construct a clean dataframe manually.
        df = pd.read_excel(excel_file, sheet_name='数据表（两个细则系统）', header=[0], engine='openpyxl')
        
        # The key columns we need are:
        # 厂站, 免考情况, and various "考核电量" columns.
        # Required: 功率预测总考核电量, 一次调频总考核电量.
        
        # In the provided sample:
        # Row 0 has "厂站" at col 2 (0-based index likely).
        # We need to find the column index for "厂站", "免考情况"
        
        # Let's clean up column names. The header seems to be scattered.
        # We will iterate columns and find the ones we need.
        
        # Simplify: Rename columns based on their content in the first valid header row.
        # The sample output showed:
        #   Unnamed: 2 -> 厂站
        #   Unnamed: 3 -> 免考情况
        #   ... -> 功率预测总考核电量（MWH）
        
        # Let's reload with header=0 and inspect columns.
        # Actually, let's use the layout from the `run_command` output.
        # 0: NaN, 年月, 厂站, 免考情况...
        
        # Strategy: find the column index for '厂站' and '免考情况'
        cols = df.columns.tolist()
        
        # Rename columns map
        rename_map = {}
        for col in cols:
            # If the column name itself or the first row value contains the target
            if '厂站' in str(col):
                rename_map[col] = 'Station'
            elif '免考情况' in str(col):
                rename_map[col] = 'ExemptionStatus'
            elif '功率预测总考核电量' in str(col):
                rename_map[col] = 'PowerPredAssessment'
            # Add more fields as needed
        
        # If headers are in the first row of data (which is common in these reports)
        # The `run_command` output showed "Unnamed: 2" has "厂站" in row 0.
        # So `pd.read_excel(..., header=0)` might have put "名称" as the header for col 0.
        
        # Strategy: find the header row by looking for key markers
        first_valid_row = -1
        for i, row in df.iterrows():
            row_str = " ".join([str(x) for x in row.tolist()])
            if '厂站' in row_str and '年月' in row_str:
                df.columns = row.tolist()
                df = df.iloc[i+1:].reset_index(drop=True)
                break
        
        # Now columns should be "厂站", "免考情况", etc.
        # Normalize columns
        df.columns = [str(c).strip() for c in df.columns]
        
        # Filter valid rows (where Station is not NaN)
        df = df.dropna(subset=['厂站'])
        df = df[df['厂站'] != '厂站'] # Remove repeated headers if any
        
        # Clean numeric columns
        # We need to identify which columns are "PowerPredAssessment" etc.
        # Name variations: "功率预测总考核电量" or "功率预测总考核电量（MWH）"
        
        # Fuzzy find columns
        def find_col(keywords):
            for c in df.columns:
                if all(k in c for k in keywords):
                    return c
            return None

        col_power_pred = find_col(['功率预测', '总考核电量'])
        col_primary_freq = find_col(['一次调频', '总考核电量'])

        # Fix Date and Station columns
        station_col = find_and_rename(df, ['厂站', '电厂名称', '名称'])
        if station_col:
            df['Station'] = df[station_col].apply(normalize_station_name)
        
        date_col = find_and_rename(df, ['日期', '日期（文本）', '年月'])
        if date_col:
            df['Date'] = df[date_col].apply(format_excel_date)
        else:
            df['Date'] = '未知'

        ex_status_col = find_and_rename(df, ['免考情况'])
        if ex_status_col:
            df['ExemptionStatus'] = df[ex_status_col]
        else:
            df['ExemptionStatus'] = '未知'

        if col_power_pred:
            df['PowerAssessmentVal'] = df[col_power_pred].apply(clean_numeric)
        else:
            df['PowerAssessmentVal'] = 0.0

        return df[['Station', 'ExemptionStatus', 'PowerAssessmentVal', 'Date']]

    except Exception as e:
        print(f"Error loading main table: {e}")
        return pd.DataFrame()

def load_summary_tables(excel_file):
    """
    Load summary tables:
    A: 结算汇总表 (Profit/Loss)
    B: 考核汇总表 (Assessment Breakdown)
    C: 辅助服务补偿汇总表 (Compensation)
    """
    results = {}
    
    # 1. 结算汇总表 (Profit/Loss)
    try:
        df_settlement = pd.read_excel(excel_file, sheet_name='公示-表一、结算汇总表', engine='openpyxl')
        # Row 0 might be header, check columns
        if '电厂名称' not in df_settlement.columns:
             # Try finding header row
            for i, row in df_settlement.iterrows():
                if '电厂名称' in row.astype(str).tolist():
                    df_settlement.columns = row
                    df_settlement = df_settlement.iloc[i+1:].reset_index(drop=True)
                    break
        
        df_settlement.columns = [str(c).strip() for c in df_settlement.columns]
        df_settlement = df_settlement.dropna(subset=['电厂名称'])
        
        # Fix Date and Station columns
        station_col = find_and_rename(df_settlement, ['厂站', '电厂名称', '名称'])
        if station_col:
            df_settlement['Station'] = df_settlement[station_col].apply(normalize_station_name)
        
        date_col = find_and_rename(df_settlement, ['日期', '日期（文本）', '年月'])
        if date_col:
            df_settlement['Date'] = df_settlement[date_col].apply(format_excel_date)
        else:
            df_settlement['Date'] = '未知'

        # Clean columns
        df_settlement['Station'] = df_settlement['电厂名称'].apply(normalize_station_name)
        df_settlement['NetIncome'] = df_settlement['“两个细则”结算净收入'].apply(clean_numeric)
        df_settlement['AssessmentCost'] = df_settlement['“两个细则”考核费用'].apply(clean_numeric)
        df_settlement['CompensationIncome'] = df_settlement['“两个细则”补偿费用'].apply(clean_numeric)
        
        results['settlement'] = df_settlement[['Station', 'NetIncome', 'AssessmentCost', 'CompensationIncome', 'Date']]
    except Exception as e:
        print(f"Error loading 结算汇总表: {e}")
        results['settlement'] = pd.DataFrame()

    # 2. 考核汇总表 (Assessment Breakdown) - Separated
    try:
        # 2a. Load Assessment Quantity (MWh) from '数据表（两个细则系统）'
        try:
            df_mwh = pd.read_excel(excel_file, sheet_name='数据表（两个细则系统）', engine='openpyxl')
            
            # Header logic for '数据表'
            header_keys = ['厂站', '场站', '电厂名称', '名称']
            for i, row in df_mwh.iterrows():
                row_vals = [str(x) for x in row.tolist()]
                if any(k in row_vals for k in header_keys):
                    df_mwh.columns = row
                    df_mwh = df_mwh.iloc[i+1:].reset_index(drop=True)
                    break
            
            # Standardize
            df_mwh.columns = [str(c).replace('\n', '').strip() for c in df_mwh.columns]
            station_col = find_and_rename(df_mwh, ['厂站', '场站', '电厂名称', '名称'])
            if station_col: df_mwh.rename(columns={station_col: 'Station'}, inplace=True)
            
            # Date
            date_col = find_and_rename(df_mwh, ['日期', '日期（文本）', '年月'])
            if date_col:
                df_mwh['Date'] = df_mwh[date_col].apply(format_excel_date)
            else:
                df_mwh['Date'] = '未知'
                
            # Filter Exemption rows if present
            if '免考情况' in df_mwh.columns:
                df_mwh = df_mwh[df_mwh['免考情况'].str.contains('免考后', na=True)]
                
            # Clean numeric
            df_mwh = df_mwh.dropna(subset=['Station'])
            df_mwh['Station'] = df_mwh['Station'].apply(normalize_station_name)
            exclude_cols = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '考核费用合计', '上网电量', 'Date', '名称', '年月', '免考情况', '合计']
            mwh_items = [c for c in df_mwh.columns if c not in exclude_cols and 'Unnamed' not in c]
            for col in mwh_items:
                df_mwh[col] = df_mwh[col].apply(clean_numeric)
                
            results['assessment_mwh'] = df_mwh
        except Exception as e:
            print(f"Error loading Assessment MWh: {e}")
            results['assessment_mwh'] = pd.DataFrame()

        # 2b. Load Assessment Cost (Yuan) from '公示-表二、并网运行考核汇总表'
        try:
            df_cost = pd.read_excel(excel_file, sheet_name='公示-表二、并网运行考核汇总表', engine='openpyxl')
            
            # Header logic (usually standard header)
            
            # Standardize
            df_cost.columns = [str(c).replace('\n', '').strip() for c in df_cost.columns]
            station_col = find_and_rename(df_cost, ['厂站', '场站', '电厂名称', '名称'])
            if station_col: df_cost.rename(columns={station_col: 'Station'}, inplace=True)
            
            # Date
            date_col = find_and_rename(df_cost, ['日期', '日期（文本）', '年月'])
            if date_col:
                df_cost['Date'] = df_cost[date_col].apply(format_excel_date)
            else:
                df_cost['Date'] = '未知'
                
            # Clean numeric
            df_cost = df_cost.dropna(subset=['Station'])
            df_cost['Station'] = df_cost['Station'].apply(normalize_station_name)
            exclude_cols = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '考核费用合计', '上网电量', 'Date', '名称', '年月', '免考情况', '合计']
            cost_items = [c for c in df_cost.columns if c not in exclude_cols and 'Unnamed' not in c]
            for col in cost_items:
                df_cost[col] = df_cost[col].apply(clean_numeric)
                
            results['assessment_cost'] = df_cost
            # Backwards compatibility / default for details if needed
            results['assessment_detail'] = df_cost 
        except Exception as e:
            print(f"Error loading Assessment Cost: {e}")
            results['assessment_cost'] = pd.DataFrame()
            
    except Exception as e:
        print(f"Error in assessment loading block: {e}")
    # 3. 辅助服务补偿汇总表 (Compensation Breakdown)
    try:
        df_comp = pd.read_excel(excel_file, sheet_name='公示-表四、辅助服务补偿汇总表', engine='openpyxl')
        if '电厂名称' not in df_comp.columns:
            for i, row in df_comp.iterrows():
                if '电厂名称' in row.astype(str).tolist():
                    df_comp.columns = row
                    df_comp = df_comp.iloc[i+1:].reset_index(drop=True)
                    break
        
        df_comp.columns = [str(c).strip() for c in df_comp.columns]
        df_comp = df_comp.dropna(subset=['电厂名称'])
        df_comp['Station'] = df_comp['电厂名称'].apply(normalize_station_name)
        
        # Identify comp columns (usually positive)
        # Identify comp columns (usually positive)
        exclude_cols_comp = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '补偿费用合计', '上网电量', 'Date']
        
        # Fix Date and Station columns
        station_col = find_and_rename(df_comp, ['厂站', '电厂名称', '名称'])
        if station_col:
            df_comp['Station'] = df_comp[station_col].apply(normalize_station_name)
        
        date_col = find_and_rename(df_comp, ['日期', '日期（文本）', '年月'])
        if date_col:
            df_comp['Date'] = df_comp[date_col].apply(format_excel_date)
        else:
            df_comp['Date'] = '未知'
            
        comp_items = [c for c in df_comp.columns if c not in exclude_cols_comp]
        
        for col in comp_items:
            df_comp[col] = df_comp[col].apply(clean_numeric)
            
        results['comp_detail'] = df_comp
    except Exception as e:
        print(f"Error loading 补偿汇总表: {e}")
        results['comp_detail'] = pd.DataFrame()

    return results

    return results

def analyze_excel(filepath, output_path, period=None, station=None):
    """
    Main analysis orchestrator.
    """
    # Load data
    df_main = load_main_table(filepath) # From '数据表（两个细则系统）'
    summary_data = load_summary_tables(filepath)
    
    df_settlement = summary_data.get('settlement', pd.DataFrame())
    df_assessment_cost = summary_data.get('assessment_cost', pd.DataFrame())
    df_assessment_mwh = summary_data.get('assessment_mwh', pd.DataFrame())
    df_comp = summary_data.get('comp_detail', pd.DataFrame())
    
    # Collect all available periods from all dataframes
    all_dates = []
    for df_temp in [df_settlement, df_assessment_cost, df_assessment_mwh, df_comp, df_main]:
        if not df_temp.empty and 'Date' in df_temp.columns:
            # Ensure every single date in the column is formatted
            df_temp['Date'] = df_temp['Date'].apply(format_excel_date)
            all_dates.extend(df_temp['Date'].unique().tolist())
    
    # Final pass safety net
    formatted_dates = [format_excel_date(d) for d in all_dates if d != '未知']
    available_periods = sorted(list(set(formatted_dates)), reverse=True)
    
    available_stations = []
    if not df_settlement.empty:
        available_stations = sorted(df_settlement['Station'].unique().tolist())
    
    analysis_results = {
        'available_periods': available_periods,
        'available_stations': available_stations,
        'selected_period': period or 'all',
        'selected_station': station or 'all'
    }
    
    # Filtering if period specified
    if period and period != 'all':
        if not df_settlement.empty and 'Date' in df_settlement.columns: 
            df_settlement = df_settlement[df_settlement['Date'] == period]
        if not df_assessment_cost.empty and 'Date' in df_assessment_cost.columns: 
            df_assessment_cost = df_assessment_cost[df_assessment_cost['Date'] == period]
        if not df_assessment_mwh.empty and 'Date' in df_assessment_mwh.columns: 
            df_assessment_mwh = df_assessment_mwh[df_assessment_mwh['Date'] == period]
        if not df_comp.empty and 'Date' in df_comp.columns: 
            df_comp = df_comp[df_comp['Date'] == period]
        if not df_main.empty and 'Date' in df_main.columns: 
            df_main = df_main[df_main['Date'] == period]

    # Filtering if station specified
    if station and station != 'all':
        if not df_settlement.empty: df_settlement = df_settlement[df_settlement['Station'] == station]
        if not df_assessment_cost.empty: df_assessment_cost = df_assessment_cost[df_assessment_cost['Station'] == station]
        if not df_assessment_mwh.empty: df_assessment_mwh = df_assessment_mwh[df_assessment_mwh['Station'] == station]
        if not df_comp.empty: df_comp = df_comp[df_comp['Station'] == station]
        if not df_main.empty: df_main = df_main[df_main['Station'] == station]
    
    # Aggregate data by station if multiple entries exist
    if not df_settlement.empty:
        # Use only numeric columns for sum to avoid TypeError
        df_settlement = df_settlement.groupby('Station').sum(numeric_only=True).reset_index()
    
    # Aggregate Cost
    if not df_assessment_cost.empty:
        exclude_cols_asm = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '考核费用合计', '上网电量', 'Date', '名称', '年月', '免考情况', '合计']
        num_cols_cost = [c for c in df_assessment_cost.columns if c not in exclude_cols_asm and not str(c).startswith('Unnamed')]
        df_assessment_cost = df_assessment_cost.groupby('Station')[num_cols_cost].sum().reset_index()

    # Aggregate MWh
    if not df_assessment_mwh.empty:
        exclude_cols_asm = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '考核费用合计', '上网电量', 'Date', '名称', '年月', '免考情况', '合计']
        num_cols_mwh = [c for c in df_assessment_mwh.columns if c not in exclude_cols_asm and not str(c).startswith('Unnamed')]
        df_assessment_mwh = df_assessment_mwh.groupby('Station')[num_cols_mwh].sum().reset_index()

    if not df_comp.empty:
        exclude_cols_comp = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '补偿费用合计', '上网电量', 'Date']
        num_cols_comp = [c for c in df_comp.columns if c not in exclude_cols_comp and not str(c).startswith('Unnamed')]
        df_comp = df_comp.groupby('Station')[num_cols_comp].sum().reset_index()
    
    # 1. 经营损益分析 (Rankings)
    if not df_settlement.empty:
        # Sort by Net Income (Ascending = Max Loss first)
        df_sorted_loss = df_settlement.sort_values(by='NetIncome', ascending=True)
        top_loss_stations = df_sorted_loss.to_dict('records')
        
        df_sorted_profit = df_settlement.sort_values(by='NetIncome', ascending=False)
        top_profit_stations = df_sorted_profit.to_dict('records')
        
        # Compensation Ranking
        df_sorted_comp = df_settlement.sort_values(by='CompensationIncome', ascending=False)
        top_comp_stations = df_sorted_comp.to_dict('records')
        
        analysis_results['profit_ranking'] = {
            'top_loss': top_loss_stations,
            'top_profit': top_profit_stations,
            'top_comp': top_comp_stations,
            'full': df_sorted_loss.to_dict('records')
        }
        
    # 2. 考核动因分析 (Grouped breakdown based on updated taxonomy)
    groups = {
        '技术指导与管理': [
            '一次调频和自动发电控制', '继电保护与安自装置', '励磁系统和PSS装置', 
            '通信设备装置', '自动化装置', '电力监控系统', '并网检测与仿真', 
            '电气设备', '水库调度运行', '低(零)电压穿越', '动态无功装置', 
            '风光AGC', '风光AVC', '风光母线', '网络安全', '信息报送',
            '技术指导', '运行管理'
        ],
        '发电计划': ['发电计划'],
        '一次调频': ['一次调频'],
        '母线电压': ['母线电压'],
        '非停': ['非停'],
        '调峰': ['调峰'],
        '燃料管理': ['燃料管理'],
        '黑启动': ['黑启动'],
        '水电振动区': ['水电振动区'],
        'AVC': ['AVC'],
        '功率预测': ['功率预测', '预测上报率', '预测准确率'],
        '有功功率变化率': ['有功功率变化率', '变化率'],
        '脱网': ['脱网'],
        '数据质量': ['数据质量', '数据合格率', '质量', '传输', '通信', '合格率'],
        '安全管理': ['安全管理'],
        '调度管理': ['调度管理'],
        '检修管理': ['检修管理'],
        '其他': ['其他']
    }

    if not df_assessment_cost.empty:
        exclude_cols = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '考核费用合计', '上网电量', 'Date', '名称', '年月', '免考情况', '合计']
        numeric_cols_cost = [c for c in df_assessment_cost.columns if c not in exclude_cols and not str(c).startswith('Unnamed')]
        
        # Calculate raw totals
        raw_totals = df_assessment_cost[numeric_cols_cost].sum()
        
        # Group totals (with logic to avoid double counting Total vs Sub-items)
        items_by_group = {} 
        for item, val in raw_totals.items():
            if val == 0: continue
            found_group = False
            for group_name, keywords in groups.items():
                if any(k in str(item) for k in keywords):
                    items_by_group.setdefault(group_name, []).append((item, val))
                    found_group = True
                    break
            if not found_group:
                items_by_group.setdefault('其他', []).append((item, val))
                
        grouped_totals = {}
        for g_name, items in items_by_group.items():
            # If both "Total/Sum" columns and sub-items exist, prioritize sub-items to avoid double counting
            subs = [v for k, v in items if not any(x in str(k) for x in ['总考核', '总计', '合计', '小计'])]
            totals = [v for k, v in items if any(x in str(k) for x in ['总考核', '总计', '合计', '小计'])]
            grouped_totals[g_name] = sum(subs) if subs else sum(totals)
                
        # Filter zero values and sort
        analysis_results['assessment_composition'] = {k: v for k, v in grouped_totals.items() if v != 0}

    # Build a consolidated item-to-group map for frontend drill-down (Cost & Mwh)
    item_group_map = {}
    all_numeric_cols = set()
    if not df_assessment_cost.empty:
        all_numeric_cols.update([c for c in df_assessment_cost.columns if c not in ['Station', 'Date', '日期', '日期（文本）', '电厂名称', '电厂类型', '结算序号', '合计', '考核费用合计', '上网电量', '名称', '年月', '免考情况'] and not str(c).startswith('Unnamed')])
    if not df_assessment_mwh.empty:
        all_numeric_cols.update([c for c in df_assessment_mwh.columns if c not in ['Station', 'Date', '日期', '日期（文本）', '电厂名称', '电厂类型', '结算序号', '合计', '考核费用合计', '上网电量', '名称', '年月', '免考情况'] and not str(c).startswith('Unnamed')])

    for item in all_numeric_cols:
        found_group = False
        for group_name, keywords in groups.items():
            if any(k in str(item) for k in keywords):
                item_group_map[item] = group_name
                found_group = True
                break
        if not found_group:
            item_group_map[item] = '其他'
    
    analysis_results['item_group_map'] = item_group_map

    # 3. High-impact stations per category (Highlights using Mwh)
    highlights = {}
    if not df_assessment_mwh.empty:
        # Find max for specific key categories (with variations)
        category_aliases = {
            '技术指导与管理': ['技术指导与管理总考核电量（MWH）', '技术指导与管理', '技术指导'],
            '功率预测': ['功率预测总考核电量（MWH）', '功率预测总考核电量', '风电(光伏)功率预测', '风电功率预测', '光伏功率预测', '功率预测'],
            '数据合格率': ['数据合格率总考核电量（MWH）', '数据合格率总考核电量', '风电(光伏)数据合格率', '数据合格率', '场站数据合格率']
        }
        
        # Define station types (Basic heuristic based on name)
        wind_stations = df_assessment_mwh[df_assessment_mwh['Station'].str.contains('风电', na=False)]
        solar_stations = df_assessment_mwh[df_assessment_mwh['Station'].str.contains('光伏', na=False)]
        
        # Helper to find column by aliases
        def get_best_col(aliases):
            for a in aliases:
                if a in df_assessment_mwh.columns: return a
            return None

        for label, aliases in category_aliases.items():
            cat = get_best_col(aliases)
            if cat:
                # Use absolute value to ignore sign differences
                df_assessment_mwh['abs_' + cat] = df_assessment_mwh[cat].abs()
                
                # Overall top
                top = df_assessment_mwh.sort_values(by='abs_' + cat, ascending=False).iloc[0]
                highlights[label] = {
                    'station': top['Station'],
                    'amount': top[cat],
                    'type': '总体'
                }
                
                # Wind top
                if not wind_stations.empty:
                    wind_df = wind_stations.copy()
                    wind_df['abs_' + cat] = wind_df[cat].abs()
                    top_wind = wind_df.sort_values(by='abs_' + cat, ascending=False).iloc[0]
                    highlights[label + '_wind'] = {
                        'station': top_wind['Station'],
                        'amount': top_wind[cat],
                        'type': '风电'
                    }

                # Solar top
                if not solar_stations.empty:
                    solar_df = solar_stations.copy()
                    solar_df['abs_' + cat] = solar_df[cat].abs()
                    top_solar = solar_df.sort_values(by='abs_' + cat, ascending=False).iloc[0]
                    highlights[label + '_solar'] = {
                        'station': top_solar['Station'],
                        'amount': top_solar[cat],
                        'type': '光伏'
                    }

        # Cleanup helper columns starting with 'abs_'
        abs_cols = [c for c in df_assessment_mwh.columns if str(c).startswith('abs_')]
        if abs_cols:
            df_assessment_mwh = df_assessment_mwh.drop(columns=abs_cols)

    analysis_results['category_highlights'] = highlights

    # 2.5 补偿动因分析 (Total breakdown)
    if not df_comp.empty:
        exclude_cols_comp = ['结算序号', '电厂类型', '电厂名称', 'Station', '日期', '日期（文本）', '补偿费用合计', '上网电量', 'Date']
        numeric_cols_comp = [c for c in df_comp.columns if c not in exclude_cols_comp]
        
        total_comp_by_item = df_comp[numeric_cols_comp].sum().sort_values(ascending=False)
        # Filter for positive compensation
        comp_composition = total_comp_by_item[total_comp_by_item > 0].to_dict()
        analysis_results['comp_composition'] = comp_composition

    # 3. 免考与申诉 (Exemption & Appeal)
    # Using df_main
    if not df_main.empty:
        # Exemption Logic: "PowerPredAssessment" diff for '免考前' vs '免考后'
        # Group by Station and ExemptionStatus
        
        # Ensure we have required columns for pivot
        if 'Station' in df_main.columns and 'ExemptionStatus' in df_main.columns and 'PowerAssessmentVal' in df_main.columns:
            pivot_df = df_main.pivot_table(index='Station', columns='ExemptionStatus', values='PowerAssessmentVal', aggfunc='sum')
            
            # Ensure '免考前' and '免考后' are numeric and handle missing
            for col in ['免考前', '免考后']:
                if col in pivot_df.columns:
                    pivot_df[col] = pd.to_numeric(pivot_df[col], errors='coerce').fillna(0)
                else:
                    pivot_df[col] = 0.0

            if '免考前' in pivot_df.columns and '免考后' in pivot_df.columns:
                pivot_df['ExemptionDiff'] = pivot_df['免考前'] - pivot_df['免考后']
                
                # Filter non-zero savings
                exemption_success = pivot_df[pivot_df['ExemptionDiff'] > 0].sort_values(by='ExemptionDiff', ascending=False).reset_index()
                analysis_results['exemption_effect'] = exemption_success[['Station', 'ExemptionDiff']].to_dict('records')
            
        # Appeal placeholder (needs specific column logic if available)
        analysis_results['appeal_effect'] = [] 
            
    # 4. Prepare drill-down details
    analysis_results['details'] = {
        'assessment_cost': df_assessment_cost.to_dict('records') if not df_assessment_cost.empty else [],
        'assessment_mwh': df_assessment_mwh.to_dict('records') if not df_assessment_mwh.empty else [],
        'assessment_raw': df_assessment_cost.to_dict('records') if not df_assessment_cost.empty else [], # Default fallback for compatibility
        'compensation_raw': df_comp.to_dict('records') if not df_comp.empty else []
    }
            
            # Estimate money saved?
            # We need unit price. "利用 考核费用/考核电量 估算单价".
            # For now, just return the MWh saved.
    
    # 4. Generate Excel Report
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        if not df_settlement.empty:
            df_settlement.to_excel(writer, sheet_name='经营损益排名', index=False)
        if not df_assessment_cost.empty:
            df_assessment_cost.to_excel(writer, sheet_name='考核明细(费用)', index=False)
        if not df_assessment_mwh.empty:
            df_assessment_mwh.to_excel(writer, sheet_name='考核明细(电量)', index=False)
        if not df_comp.empty:
            df_comp.to_excel(writer, sheet_name='补偿明细', index=False)
        if not df_main.empty:
            df_main.to_excel(writer, sheet_name='免考电量数据', index=False)
            if 'appeal_effect' in analysis_results:
                pd.DataFrame(analysis_results['appeal_effect']).to_excel(writer, sheet_name='申诉成效TOP5')

    return analysis_results

