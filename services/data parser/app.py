from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from analyzer_web import analyze_file
from daily_report_web import analyze_daily_report 

import json
from datetime import datetime

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
HISTORY_FILE = 'history.json'
DAILY_HISTORY_FILE = 'daily_history.json'
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

@app.route('/')
def index():
    return render_template('power_prediction.html')

@app.route('/power_prediction')
def power_prediction():
    return render_template('power_prediction.html')

@app.route('/daily_report')
def daily_report_page():
    return render_template('daily_report.html')

@app.route('/history', methods=['GET'])
def get_history():
    return jsonify(load_history())

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
            summary, error = analyze_file(filepath, app.config['OUTPUT_FOLDER'])
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


if __name__ == '__main__':

    app.run(host='0.0.0.0', port=5001, debug=True)


