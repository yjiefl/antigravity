import pandas as pd
from typing import Dict, List, Any

def compare_records(record1, record2):
    """
    Compares two analysis records.
    record1: The "Newer" record (usually) or simply the first one selected.
    record2: The "Older" record (usually) or simply the second one selected.
    We will sort them by timestamp inside to ensure logical diff (New - Old).
    """
    
    # Ensure correct chronological order (Old -> New)
    # Timestamps are YYYY-MM-DD HH:MM:SS
    t1 = record1.get('timestamp', '')
    t2 = record2.get('timestamp', '')
    
    # If t1 > t2, then r1 is newer. Change = r1 - r2.
    # If t1 < t2, then r2 is newer. Change = r2 - r1.
    if t1 > t2:
        new_rec, old_rec = record1, record2
        label_new, label_old = t1, t2
    else:
        new_rec, old_rec = record2, record1
        label_new, label_old = t2, t1

    # Basic Diffs
    diff_summary = {
        'timestamp_new': label_new,
        'timestamp_old': label_old,
        'filename_new': new_rec.get('filename', ''),
        'filename_old': old_rec.get('filename', ''),
        'total_deduction_diff': round(new_rec.get('total_deduction', 0) - old_rec.get('total_deduction', 0), 2),
        'total_cases_diff': int(new_rec.get('total_cases', 0) - old_rec.get('total_cases', 0))
    }
    
    # Station Level Diffs
    # Convert list of dicts to dict for easy lookup: {'station_name': score}
    stations_new = {item['name']: item['value'] for item in new_rec.get('top_stations', [])}
    stations_old = {item['name']: item['value'] for item in old_rec.get('top_stations', [])}
    
    all_stations = set(stations_new.keys()) | set(stations_old.keys())
    station_diffs = []
    
    for s in all_stations:
        val_new = stations_new.get(s, 0)
        val_old = stations_old.get(s, 0)
        diff = round(val_new - val_old, 2)
        if diff != 0 or val_new > 0 or val_old > 0:
            station_diffs.append({
                'name': s,
                'val_new': val_new,
                'val_old': val_old,
                'diff': diff
            })
    
    # Sort by absolute diff descending to show biggest changes first
    station_diffs.sort(key=lambda x: abs(x['diff']), reverse=True)
    
    # Item Level Diffs (Reasons) - Aggregating Points from raw_details for accuracy
    def get_item_scores(rec):
        details = rec.get('raw_details', [])
        if not details:
            # Fallback to top_items if raw_details is missing (compatibility with broken records)
            return {item['name']: item['value'] for item in rec.get('top_items', [])}
        
        # Convert list of dicts to a dict of sums: {'item_name': sum_of_deduction}
        item_map = {}
        for d in details:
            name = d.get('考核项', '未知')
            val = float(d.get('扣分值', 0))
            item_map[name] = item_map.get(name, 0) + val
        return {k: round(v, 2) for k, v in item_map.items()}

    items_new = get_item_scores(new_rec)
    items_old = get_item_scores(old_rec)
    
    all_items = set(items_new.keys()) | set(items_old.keys())
    item_diffs = []
    
    for i in all_items:
        val_new = items_new.get(i, 0)
        val_old = items_old.get(i, 0)
        diff = round(val_new - val_old, 2)
        if diff != 0 or val_new > 0 or val_old > 0:
            item_diffs.append({
                'name': i,
                'val_new': val_new,
                'val_old': val_old,
                'diff': diff
            })

    item_diffs.sort(key=lambda x: abs(x['diff']), reverse=True)

    # Matrix Level Diffs (Station x Item) for Drill-down
    def get_matrix(rec):
        details = rec.get('raw_details', [])
        matrix = {} # (station, item) -> value
        for d in details:
            s_name = d.get('厂站名', '未知')
            i_name = d.get('考核项', '未知')
            val = float(d.get('扣分值', 0))
            key = (s_name, i_name)
            matrix[key] = matrix.get(key, 0) + val
        return matrix

    matrix_new = get_matrix(new_rec)
    matrix_old = get_matrix(old_rec)
    
    all_keys = set(matrix_new.keys()) | set(matrix_old.keys())
    station_item_diffs = []
    
    for s_name, i_name in all_keys:
        v_new = round(matrix_new.get((s_name, i_name), 0), 2)
        v_old = round(matrix_old.get((s_name, i_name), 0), 2)
        diff = round(v_new - v_old, 2)
        if diff != 0 or v_new > 0 or v_old > 0:
            station_item_diffs.append({
                'station': s_name,
                'item': i_name,
                'val_new': v_new,
                'val_old': v_old,
                'diff': diff
            })

    return {
        'meta': diff_summary,
        'station_diffs': station_diffs,
        'item_diffs': item_diffs,
        'station_item_diffs': station_item_diffs, # New granular data
        'raw_new': new_rec.get('raw_details', []),
        'raw_old': old_rec.get('raw_details', [])
    }

def generate_compare_excel(record1, record2, output_path):
    data = compare_records(record1, record2)
    meta = data['meta']
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # 1. 总体差异概览
        summary_df = pd.DataFrame([{
            '指标': '总扣分差异',
            '基准期(旧)': record2.get('total_deduction', 0) if meta['timestamp_old'] == record2.get('timestamp') else record1.get('total_deduction', 0),
            '对照期(新)': record1.get('total_deduction', 0) if meta['timestamp_new'] == record1.get('timestamp') else record2.get('total_deduction', 0),
            '差异量': meta['total_deduction_diff'],
            '状态': '恶化' if meta['total_deduction_diff'] > 0 else '改善'
        }])
        summary_df.to_excel(writer, index=False, sheet_name='总体差异概览')
        
        # 2. 场站波动榜
        pd.DataFrame(data['station_diffs']).to_excel(writer, index=False, sheet_name='场站波动排行')
        
        # 3. 考核项波动榜
        pd.DataFrame(data['item_diffs']).to_excel(writer, index=False, sheet_name='指标趋势变动')
        
        # 4. 穿透细节矩阵
        pd.DataFrame(data['station_item_diffs']).to_excel(writer, index=False, sheet_name='场站指标穿透矩阵')

def generate_compare_pdf(record1, record2, output_path):
    from analyzer_web import BetterPDF
    import os
    
    data = compare_records(record1, record2)
    meta = data['meta']
    
    pdf = BetterPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    if not pdf.font_loaded:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, "Chinese Font Load Failed.")
        pdf.output(output_path)
        return

    # 一、对比概览
    pdf.set_font('Chinese', '', 16)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 12, '01 | 两期历史记录对比分析概览', 0, 1)
    
    pdf.set_font('Chinese', '', 11)
    pdf.set_text_color(75, 85, 99)
    pdf.cell(0, 8, f"基准期 (旧): {meta['filename_old']} ({meta['timestamp_old']})", 0, 1)
    pdf.cell(0, 8, f"对照期 (新): {meta['filename_new']} ({meta['timestamp_new']})", 0, 1)
    
    diff_val = meta['total_deduction_diff']
    status = "恶化 ⚠️" if diff_val > 0 else "改善 ✅"
    pdf.set_font('Chinese', '', 12)
    pdf.set_text_color(220, 38, 38) if diff_val > 0 else pdf.set_text_color(16, 185, 129)
    pdf.cell(0, 10, f"扣分总额差异: {diff_val:+} 分 ({status})", 0, 1)
    pdf.ln(10)

    # 二、场站波动 Top 榜
    pdf.set_text_color(31, 41, 55)
    pdf.set_font('Chinese', '', 14)
    pdf.cell(0, 10, '02 | 重点场站波动排行 (TOP Changes)', 0, 1)
    pdf.set_font('Chinese', '', 10)
    pdf.set_fill_color(249, 250, 251)
    pdf.cell(80, 10, ' 场站名称', 1, 0, 'L', True)
    pdf.cell(35, 10, ' 旧值 ', 1, 0, 'C', True)
    pdf.cell(35, 10, ' 新值 ', 1, 0, 'C', True)
    pdf.cell(35, 10, ' 波动差异 ', 1, 1, 'C', True)
    
    for s in data['station_diffs'][:15]: # Show top 15
        pdf.cell(80, 9, f"  {s['name']}", 1)
        pdf.cell(35, 9, f"{s['val_old']} ", 1, 0, 'R')
        pdf.cell(35, 9, f"{s['val_new']} ", 1, 0, 'R')
        pdf.set_text_color(220, 38, 38) if s['diff'] > 0 else pdf.set_text_color(16, 185, 129)
        pdf.cell(35, 9, f"{s['diff']:+} ", 1, 1, 'R')
        pdf.set_text_color(31, 41, 55)
    pdf.ln(12)

    # 三、穿透深度分析
    pdf.add_page()
    pdf.set_font('Chinese', '', 14)
    pdf.cell(0, 12, '03 | 重点场站指标穿透解析', 0, 1)
    
    # Group by station for granular display
    grouped_diffs = {}
    for d in data['station_item_diffs']:
        grouped_diffs.setdefault(d['station'], []).append(d)
        
    # Only show top 8 stations with biggest changes
    sorted_stations = sorted(grouped_diffs.keys(), key=lambda s: sum(abs(x['diff']) for x in grouped_diffs[s]), reverse=True)[:8]
    
    for s_name in sorted_stations:
        pdf.set_font('Chinese', '', 12)
        pdf.set_fill_color(238, 242, 255)
        pdf.cell(0, 10, f" 场站：{s_name}", 1, 1, 'L', True)
        
        pdf.set_font('Chinese', '', 9)
        for item in sorted(grouped_diffs[s_name], key=lambda x: abs(x['diff']), reverse=True):
            status_tag = "⚠️" if item['diff'] > 0 else "✅"
            pdf.cell(10)
            row_text = f"• {item['item']}: {item['val_old']} -> {item['val_new']} (差异: {item['diff']:+} {status_tag})"
            pdf.cell(0, 8, row_text, 0, 1)
        pdf.ln(5)

    pdf.output(output_path)

