import pandas as pd
import re
import os
import uuid
from fpdf import FPDF

# 目标场站列表
TARGET_STATIONS = [
    '守旗光伏电站', '岑凡光伏电站', '弄滩光伏电站', '强胜光伏电站', '派岸光伏电站', 
    '浦峙光伏电站', '峙书光伏电站', '康宁光伏电站', '寨安光伏电站', '坤山风电场', 
    '樟木光伏电站', '榕木光伏电站', '樟木风电场', '驮堪光伏电站', '把荷风电场', '武安风电场'
]

class BetterPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.font_loaded = False
        # 扩展字体搜索路径，特别是针对 Docker 环境
        possible_fonts = [
            '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', # Debian/Docker
            '/System/Library/Fonts/STHeiti Light.ttc',        # macOS
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Supplemental/Songti.ttc',
            'C:\\Windows\\Fonts\\simhei.ttf',               # Windows
            'C:\\Windows\\Fonts\\msyh.ttc'
        ]
        for f in possible_fonts:
            if os.path.exists(f):
                try:
                    self.add_font('Chinese', '', f, uni=True)
                    self.font_loaded = True
                    break
                except: continue

    def header(self):
        if self.font_loaded:
            self.set_font('Chinese', '', 14)
            self.set_text_color(67, 56, 202) # Indigo 700
            self.cell(0, 12, '新能源功率预测扣分汇总分析报告', 0, 1, 'L')
            self.set_draw_color(99, 102, 241)
            self.line(10, 22, 200, 22)
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        if self.font_loaded:
            self.set_font('Chinese', '', 8)
            self.set_text_color(150, 150, 150)
            self.cell(0, 10, f'第 {self.page_no()} 页', 0, 0, 'C')

def generate_structured_pdf(df, output_path):
    pdf = BetterPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    if not pdf.font_loaded:
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, "Chinese Font Load Failed. Defaulting to Helvetica (English only).")
        pdf.output(output_path)
        return

    # 一、核心数据快报
    pdf.set_font('Chinese', '', 16)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 12, '01 | 核心数据运营快报', 0, 1)
    
    pdf.set_font('Chinese', '', 11)
    pdf.set_text_color(75, 85, 99)
    total_deduction = round(df['扣分值'].sum(), 2)
    pdf.cell(0, 8, f"统计期间累计扣分: {total_deduction} 分", 0, 1)
    pdf.cell(0, 8, f"异常诊断时刻总数: {len(df)} 处", 0, 1)
    pdf.cell(0, 8, f"生成日期: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    pdf.ln(10)

    # 二、场站分析排行 (表格形式)
    pdf.set_font('Chinese', '', 16)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(0, 12, '02 | 场站扣分热度排行', 0, 1)
    
    station_agg = df.groupby('厂站名')['扣分值'].sum().sort_values(ascending=False).head(10)
    pdf.set_font('Chinese', '', 10)
    pdf.set_fill_color(249, 250, 251)
    pdf.cell(100, 10, ' 场站名称', 1, 0, 'L', True)
    pdf.cell(80, 10, ' 累计扣分额度 ', 1, 1, 'C', True)
    
    for name, val in station_agg.items():
        pdf.cell(100, 9, f"  {name}", 1)
        pdf.cell(80, 9, f"{round(val, 2)} ", 1, 1, 'R')
    pdf.ln(12)

    # 三、各场站深度穿透
    pdf.add_page()
    pdf.set_font('Chinese', '', 16)
    pdf.cell(0, 12, '03 | 重点场站问题深度穿透', 0, 1)
    pdf.ln(5)

    grouped = df.groupby('厂站名')
    for station_name, s_data in grouped:
        # 跳过扣分极小的场站以节省篇幅
        if s_data['扣分值'].sum() < 0.1: continue
        
        pdf.set_font('Chinese', '', 13)
        pdf.set_fill_color(238, 242, 255)
        pdf.cell(0, 10, f" 场站：{station_name} (小计: {round(s_data['扣分值'].sum(), 2)} 分)", 1, 1, 'L', True)
        
        # 按类别细分
        item_agg = s_data.groupby('考核项')['扣分值'].sum().sort_values(ascending=False)
        pdf.set_font('Chinese', '', 10)
        pdf.cell(0, 8, "   [ 扣分构成 ]:", 0, 1)
        for item_name, item_val in item_agg.items():
            pdf.cell(15)
            pdf.cell(0, 7, f"• {item_name}: 累计扣除 {round(item_val, 2)} 分", 0, 1)
        
        # 列出该站典型明细
        pdf.ln(2)
        pdf.set_font('Chinese', '', 9)
        pdf.set_text_color(107, 114, 128)
        pdf.cell(10)
        pdf.cell(180, 6, "典型扣分时刻轨迹预览:", 'B', 1)
        # 只取前5条代表性数据
        for _, row in s_data.head(5).iterrows():
            pdf.cell(10)
            reason_clean = str(row['具体原因']).replace('\n', ' ')
            row_text = f"{row['日期']} {row['时刻']} | {row['考核项']} | -{row['扣分值']}"
            pdf.cell(0, 7, row_text, 0, 1)
            pdf.cell(15)
            pdf.cell(0, 6, f"原因: {reason_clean[:60]}...", 0, 1)
        
        pdf.set_text_color(0, 0, 0)
        pdf.ln(8)

    pdf.output(output_path)

def parse_deduction_text(text):
    if pd.isna(text) or not str(text).strip(): return None
    text = str(text)
    
    # 1. 尝试更灵活的正则匹配 (支持全角/半角冒号，支持嵌套格式)
    item_match = re.search(r'考核条件[:：]\s*([^，,（\s；;]+)', text)
    score_match = re.search(r'得分[:：]\s*([\d.]+)', text)
    total_match = re.search(r'总分[:：]?\s*\(?([\d.]+)\)?', text)
    
    item_val = item_match.group(1).strip() if item_match else None
    score_val = float(score_match.group(1)) if score_match else 0.0
    total_val = float(total_match.group(1)) if total_match else 0.0
    
    # 2. 如果没找到“考核条件”，尝试通过关键词进行“智能推断” (解决限电等无前缀情况)
    if not item_val:
        if '限电' in text: item_val = "限电记录考核"
        elif '状态容量' in text: item_val = "状态容量一致性"
        elif '气象信息' in text: item_val = "气象数据考核"
        elif '预测数据' in text: item_val = "预测数据质量"
        else: item_val = "专项业务考核" # 兜底名，比“未知”好听
        
    # 3. 计算扣分 (总分 - 得分)
    deduction = round(total_val - score_val, 2)
    
    # 针对某些只写了分值的特殊情况进行补正
    if deduction <= 0 and total_val == 0:
        # 尝试从文本寻找类似 "-20" 或 "扣除X分" 的描述
        deduct_hint = re.search(r'扣除?([\d.]+)分', text)
        if deduct_hint:
            deduction = float(deduct_hint.group(1))
            
    # 4. 提取原因 (去掉前面的冗余日期时间)
    reason_clean = re.sub(r'^\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2}', '', text).strip()
    
    return {'考核项': item_val, '扣分值': deduction, '原因': reason_clean}


def analyze_file(input_path, output_dir):
    # Detect file type
    # If the user uploaded an Excel file, try to read it as Excel first
    if input_path.endswith(('.xlsx', '.xls')):
        try:
             df = pd.read_excel(input_path)
        except Exception as e:
            return None, f"Excel 文件读取失败: {str(e)}"
    else:
        # Try to read as CSV with encoding detection
        encodings = ['utf-8', 'gb18030', 'gbk', 'mbcs', 'latin1']
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(input_path, encoding=enc)
                break
            except Exception:
                continue
        
        if df is None:
             # If all text encodings fail, maybe it is an Excel file renamed as .csv?
             try:
                 df = pd.read_excel(input_path)
             except:
                 return None, "文件编码识别失败，请确保上传的是标准 CSV 或 Excel 文件"
    
        
    # Normalize column names (handle potential whitespace)
    df.columns = df.columns.astype(str).str.strip()
    
    if '厂站名' not in df.columns:
        # UX Improvement: Detect if user uploaded a Daily Report by mistake
        if any(keyword in str(df.columns) or keyword in str(df.values)[:500] for keyword in ['运营日报', '非计划损失', '限电率']):
             return None, "缺关键列 '厂站名'。检测到您可能上传了【运营日报】，请切换到顶部导航栏的【运营日报审核】页面进行操作。"
        return None, f"文件缺少关键列: '厂站名'。当前包含列: {', '.join(df.columns[:5])}..."

    df['厂站名'] = df['厂站名'].astype(str).str.strip()
    df = df[df['厂站名'].apply(lambda x: any(target in x for target in TARGET_STATIONS))]

    if df.empty: return None, "未找到目标场站数据"

    value_vars = [c for c in df.columns if '扣分详情' in c]
    df_long = df.melt(id_vars=['厂站名', '日期', '统计类型'], value_vars=value_vars, var_name='时刻', value_name='扣分详情')
    df_long['时刻'] = df_long['时刻'].str.extract(r'(\d{2}:\d{2})')
    df_long = df_long[df_long['扣分详情'].notna()]
    df_long['扣分详情'] = df_long['扣分详情'].astype(str).str.strip()
    df_long = df_long[df_long['扣分详情'] != ""]
    
    details = df_long['扣分详情'].apply(parse_deduction_text)
    df_long['考核项'] = details.apply(lambda x: x['考核项'] if x else None)
    df_long['扣分值'] = details.apply(lambda x: x['扣分值'] if x else 0.0)
    df_long['具体原因'] = details.apply(lambda x: x['原因'] if x else None)
    df_long = df_long[df_long['扣分值'] > 0]
    df_long['考核项'] = df_long['考核项'].astype(str).str.strip()

    if df_long.empty: return None, "无实际扣分记录"

    file_id = uuid.uuid4().hex[:8]
    xlsx_fname = f"report_{file_id}.xlsx"
    pdf_fname = f"report_{file_id}.pdf"
    
    xlsx_path = os.path.join(output_dir, xlsx_fname)
    pdf_path = os.path.join(output_dir, pdf_fname)
    
    # 保存结构化 Excel
    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        # 1. 总体汇总
        pd.DataFrame([{
            '总扣分': round(df_long['扣分值'].sum(), 2),
            '异常统计时刻': len(df_long),
            '分析报告ID': file_id,
            '生成时间': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')
        }]).to_excel(writer, index=False, sheet_name='总体概览')
        
        # 2. 场站分项矩阵 (Pivot Table，直观对比各站各项)
        pivot_df = df_long.pivot_table(
            index='厂站名', 
            columns='考核项', 
            values='扣分值', 
            aggfunc='sum', 
            fill_value=0
        )
        pivot_df['该站总计'] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values('该站总计', ascending=False)
        pivot_df.to_excel(writer, sheet_name='场站分项矩阵')
        
        # 3. 场站分项明细汇总 (带主要原因描述)
        station_item_agg = df_long.groupby(['厂站名', '考核项']).agg({
            '扣分值': 'sum',
            '时刻': 'count',
            '具体原因': lambda x: x.mode().iloc[0] if not x.mode().empty else x.iloc[0]
        }).reset_index()
        station_item_agg.columns = ['厂站名', '考核项', '累计扣分', '发生频率(时刻次数)', '主要扣分原因简述']
        station_item_agg.to_excel(writer, index=False, sheet_name='场站分项汇总')
        
        # 4. 原始明细
        df_long[['厂站名', '日期', '时刻', '考核项', '扣分值', '具体原因']].to_excel(writer, index=False, sheet_name='原始明细清单')


    # 生成结构化 PDF
    generate_structured_pdf(df_long, pdf_path)

    # 返回给前端的数据
    station_total = df_long.groupby('厂站名')['扣分值'].sum().sort_values(ascending=False).reset_index()
    item_total = df_long.groupby('考核项').size().sort_values(ascending=False).reset_index(name='count')
    
    res_data = {
        'file_id': file_id,
        'total_deduction': round(df_long['扣分值'].sum(), 2),
        'total_cases': len(df_long),
        'top_stations': [{'name': r['厂站名'], 'value': round(r['扣分值'], 2)} for _, r in station_total.iterrows()],
        'top_items': [{'name': r['考核项'], 'value': int(r['count'])} for _, r in item_total.iterrows()],
        'raw_details': df_long[['厂站名', '日期', '时刻', '考核项', '扣分值', '具体原因']].to_dict('records'),
        'xlsx_filename': xlsx_fname,
        'pdf_filename': pdf_fname,
        'success': True
    }

    return res_data, None
