from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from analyzer_web import analyze_file
from analyzer_compare import compare_records
from daily_report_web import analyze_daily_report 
from analyzer_two_rules import analyze_excel as analyze_two_rules

import json
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
HISTORY_FILE = 'history.json'
DAILY_HISTORY_FILE = 'daily_history.json'
TWO_RULES_HISTORY_FILE = 'two_rules_history.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def load_daily_history():
    if os.path.exists(DAILY_HISTORY_FILE):
        with open(DAILY_HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_daily_history(history):
    with open(DAILY_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

def load_two_rules_history():
    if os.path.exists(TWO_RULES_HISTORY_FILE):
        try:
            with open(TWO_RULES_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_two_rules_history(history):
    with open(TWO_RULES_HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    return render_template('power_prediction.html')

@app.route('/power_prediction')
def power_prediction():
    return render_template('power_prediction.html')

@app.route('/daily_report')
def daily_report_page():
    return render_template('daily_report.html')

@app.route('/two_rules')
def two_rules_page():
    return render_template('two_rules.html')

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(load_history())

@app.route('/compare', methods=['GET'])
def compare_history():
    id1 = request.args.get('id1')
    id2 = request.args.get('id2')
    
    if not id1 or not id2:
        return jsonify({'success': False, 'error': 'Missing file IDs'}), 400
        
    history = load_history()
    rec1 = next((item for item in history if item['file_id'] == id1), None)
    rec2 = next((item for item in history if item['file_id'] == id2), None)
    
    if not rec1 or not rec2:
         return jsonify({'success': False, 'error': 'Records not found'}), 404
         
    try:
        diff_result = compare_records(rec1, rec2)
        return jsonify({'success': True, 'data': diff_result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/history/<file_id>', methods=['DELETE'])
def delete_history(file_id):
    # Password verification
    password = request.args.get('password')
    if password != 'yj666':
        return jsonify({'success': False, 'error': '密码错误，无权删除'}), 401

    history = load_history()
    # 过滤掉要删除的记录
    new_history = [item for item in history if item['file_id'] != file_id]
    
    # 同时尝试删除物理文件
    target = next((item for item in history if item['file_id'] == file_id), None)
    if target:
        for key in ['xlsx_filename', 'pdf_filename']:
            path = os.path.join(OUTPUT_FOLDER, target[key])
            if os.path.exists(path): os.remove(path)
            
    save_history(new_history)
    return jsonify({'success': True})

@app.route('/daily_report/history', methods=['GET'])
def get_daily_history():
    return jsonify(load_daily_history())

@app.route('/daily_report/history/<file_id>', methods=['DELETE'])
def delete_daily_history(file_id):
    # Password verification
    password = request.args.get('password')
    if password != 'yj666':
        return jsonify({'success': False, 'error': '密码错误，无权删除'}), 401

    history = load_daily_history()
    target = next((item for item in history if item['file_id'] == file_id), None)
    if target:
        for key in ['json_filename', 'pdf_filename']:
            path = os.path.join(OUTPUT_FOLDER, target[key])
            if os.path.exists(path): os.remove(path)
            
    new_history = [item for item in history if item['file_id'] != file_id]
    save_daily_history(new_history)
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '无文件上传'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'})
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            filter_ceec = request.form.get('filter_ceec') == 'true'
            summary, error = analyze_file(filepath, app.config['OUTPUT_FOLDER'], filter_ceec=filter_ceec)
            if error:
                return jsonify({'success': False, 'error': error})
            
            # 记录到历史
            history = load_history()
            history.insert(0, {
                'file_id': summary['file_id'],
                'filename': file.filename,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_deduction': summary['total_deduction'],
                'total_cases': summary['total_cases'],
                'xlsx_filename': summary['xlsx_filename'],
                'pdf_filename': summary['pdf_filename'],
                'raw_details': summary['raw_details'],
                'top_stations': summary['top_stations'],
                'top_items': summary['top_items']
            })
            # 限制历史记录数量，防止 JSON 过大
            save_history(history[:50])
            
            return jsonify({'success': True, **summary})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/daily_report/upload', methods=['POST'])
def upload_daily_report():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        try:
            summary, error = analyze_daily_report(filepath, app.config['OUTPUT_FOLDER'])
            if error:
                return jsonify({'success': False, 'error': error})
            
            # 记录到历史
            history = load_daily_history()
            history.insert(0, {
                'file_id': summary['file_id'],
                'filename': file.filename,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_new_energy': summary['overview']['total_new_energy'],
                'anomaly_count': len(summary['anomalies']),
                'pdf_filename': summary['pdf_filename'],
                'json_filename': summary['json_filename'],
                'anomalies': summary['anomalies'],
                'top_curtailment': summary['top_curtailment'],
                'min_avail': summary['min_avail'],
                'overview': summary['overview']
            })
            save_daily_history(history[:50])
            
            return jsonify({'success': True, **summary})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

@app.route('/download/original/<filename>')
def download_original(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload_two_rules', methods=['POST'])
def upload_two_rules():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': '无文件上传'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '未选择文件'})
    
    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        
        try:
            output_filename = f"两细则分析报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
            
            period = request.form.get('period', 'all')
            result = analyze_two_rules(filepath, output_path, period=period)
            
            # Save history
            history = load_two_rules_history()
            history.insert(0, {
                'file_id': f"tr_{int(datetime.now().timestamp())}",
                'filename': file.filename,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'report_filename': output_filename,
                'data': result # Store analysis data for quick reloading
            })
            save_two_rules_history(history[:50])

            return jsonify({
                'success': True, 
                'report_url': f"/download/{output_filename}",
                'data': result
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

@app.route('/reanalyze_two_rules', methods=['POST'])
def reanalyze_two_rules():
    data = request.json
    filename = data.get('filename')
    period = data.get('period', 'all')
    station = data.get('station', 'all')
    
    if not filename:
        return jsonify({'success': False, 'error': 'Missing filename'})
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'Original file not found'})
        
    try:
        output_filename = f"两细则分析报告_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        result = analyze_two_rules(filepath, output_path, period=period, station=station)
        return jsonify({
            'success': True,
            'report_url': f"/download/{output_filename}",
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/two_rules/history', methods=['GET'])
def get_two_rules_history():
    return jsonify(load_two_rules_history())

@app.route('/two_rules/history/<file_id>', methods=['DELETE'])
def delete_two_rules_history(file_id):
    password = request.args.get('password')
    if password != 'yj666':
        return jsonify({'success': False, 'error': '密码错误，无权删除'}), 401
        
    history = load_two_rules_history()
    target = next((item for item in history if item['file_id'] == file_id), None)
    
    if target:
        path = os.path.join(OUTPUT_FOLDER, target['report_filename'])
        if os.path.exists(path): os.remove(path)
        
    new_history = [item for item in history if item['file_id'] != file_id]
    save_two_rules_history(new_history)
    return jsonify({'success': True})

@app.route('/two_rules/trends', methods=['GET'])
def get_two_rules_trends():
    start_period = request.args.get('start_period')
    end_period = request.args.get('end_period')
    station = request.args.get('station', 'all')
    year = request.args.get('year')
    indicator = request.args.get('indicator', 'overview')
    
    history = load_two_rules_history()
    
    # Auto-patching older history entries that lack monthly_summary
    history_updated = False
    for entry in history:
        if 'data' in entry and entry['data'].get('selected_period') == 'all' and 'monthly_summary' not in entry['data']:
            # Try to re-analyze to get the summary
            filename = entry.get('filename')
            if filename:
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if os.path.exists(filepath):
                    try:
                        from analyzer_two_rules import analyze_excel
                        # Use a dummy output path
                        dummy_out = os.path.join(app.config['OUTPUT_FOLDER'], f"temp_{entry['file_id']}.xlsx")
                        new_results = analyze_excel(filepath, dummy_out, period='all')
                        entry['data'] = new_results
                        history_updated = True
                        if os.path.exists(dummy_out): os.remove(dummy_out)
                    except Exception as e:
                        print(f"Auto-patch failed for {filename}: {e}")
    
    if history_updated:
        save_two_rules_history(history)
    
    period_map = {}
    for entry in history:
        data = entry.get('data', {})
        p = data.get('selected_period')
        if not p: continue
        
        if p != 'all':
            # Specific month entry - highest priority
            if p not in period_map:
                period_map[p] = data
        else:
            # "All" entry - extract monthly_summary if it exists and we don't have better data
            summary = data.get('monthly_summary', [])
            for m_data in summary:
                m_date = m_data.get('Date')
                if m_date and m_date not in period_map:
                    # Create a mini-data object for the trend
                    period_map[m_date] = {
                        'profit_ranking': {
                            'full': [{
                                'Station': 'all',
                                'NetIncome': m_data.get('NetIncome', 0),
                                'AssessmentCost': m_data.get('AssessmentCost', 0),
                                'CompensationIncome': m_data.get('CompensationIncome', 0)
                            }]
                        },
                        'selected_period': m_date
                    }
    
    sorted_periods = sorted(period_map.keys())
    
    if year and year != 'all':
        sorted_periods = [p for p in sorted_periods if p.startswith(year)]
    else:
        if start_period and start_period != 'all':
            sorted_periods = [p for p in sorted_periods if p >= start_period]
        if end_period and end_period != 'all':
            sorted_periods = [p for p in sorted_periods if p <= end_period]
            
    trends = {
        'periods': sorted_periods,
        'indicator': indicator
    }
    
    if indicator == 'overview':
        trends['profit'] = []
        trends['assessment'] = []
        trends['compensation'] = []
        
        for p in sorted_periods:
            data = period_map[p]
            records = data.get('profit_ranking', {}).get('full', [])
            if station == 'all':
                p_val = sum(item.get('NetIncome', 0) for item in records)
                a_val = sum(item.get('AssessmentCost', 0) for item in records)
                c_val = sum(item.get('CompensationIncome', 0) for item in records)
            else:
                target = next((item for item in records if item.get('Station') == station), None)
                p_val = target.get('NetIncome', 0) if target else 0
                a_val = target.get('AssessmentCost', 0) if target else 0
                c_val = target.get('CompensationIncome', 0) if target else 0
            
            trends['profit'].append(round(p_val, 2))
            trends['assessment'].append(round(a_val, 2))
            trends['compensation'].append(round(c_val, 2))
    else:
        # Category specific trend
        trends['values'] = []
        for p in sorted_periods:
            data = period_map[p]
            val = 0
            if station == 'all':
                # Indicators at all-station level
                val = data.get('assessment_composition', {}).get(indicator, 0)
                if val == 0:
                    val = data.get('comp_composition', {}).get(indicator, 0)
            else:
                # Extract for a specific station from detailed records?
                # This is harder since assessment_composition in history is often for 'all'
                # fallback: if the history entry was for this station, use that.
                if data.get('selected_station') == station:
                    val = data.get('assessment_composition', {}).get(indicator, 0)
                else:
                    # Very expensive: Scan detailed rows
                    # But if we have item_group_map, we can do it.
                    rows = data.get('details', {}).get('assessment_cost', [])
                    group_map = data.get('item_group_map', {})
                    for row in rows:
                        if row.get('Station') == station:
                            # Sum values for columns in this group
                            for col, group in group_map.items():
                                if group == indicator:
                                    val += float(row.get(col, 0))
                    
                    if val == 0:
                        rows_comp = data.get('details', {}).get('compensation_raw', [])
                        for row in rows_comp:
                            if row.get('Station') == station:
                                for col, group in group_map.items():
                                    if group == indicator:
                                        val += float(row.get(col, 0))

            trends['values'].append(round(val, 2))

    return jsonify({'success': True, 'trends': trends})

@app.route('/compare/export/excel')
def export_compare_excel():
    id1 = request.args.get('id1')
    id2 = request.args.get('id2')
    if not id1 or not id2: return "Missing IDs", 400
    
    history = load_history()
    rec1 = next((h for h in history if h['file_id'] == id1), None)
    rec2 = next((h for h in history if h['file_id'] == id2), None)
    if not rec1 or not rec2: return "Records not found", 404
    
    from analyzer_compare import generate_compare_excel
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"compare_{id1}_{id2}.xlsx")
    generate_compare_excel(rec1, rec2, output_path)
    
    return send_from_directory(app.config['OUTPUT_FOLDER'], f"compare_{id1}_{id2}.xlsx", as_attachment=True)

@app.route('/compare/export/pdf')
def export_compare_pdf():
    id1 = request.args.get('id1')
    id2 = request.args.get('id2')
    if not id1 or not id2: return "Missing IDs", 400
    
    history = load_history()
    rec1 = next((h for h in history if h['file_id'] == id1), None)
    rec2 = next((h for h in history if h['file_id'] == id2), None)
    if not rec1 or not rec2: return "Records not found", 404
    
    from analyzer_compare import generate_compare_pdf
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"compare_{id1}_{id2}.pdf")
    generate_compare_pdf(rec1, rec2, output_path)
    
    return send_from_directory(app.config['OUTPUT_FOLDER'], f"compare_{id1}_{id2}.pdf", as_attachment=True)

if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5001, debug=True)
