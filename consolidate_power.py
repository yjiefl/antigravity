
import pandas as pd
import os
import re

# Configuration
SOURCE_DIR = '/Users/yangjie/code/antigravity/派岸2026年日前上报功率（待AI整理）'
OUTPUT_FILE = '/Users/yangjie/code/antigravity/派岸2026年1月功率汇总.xlsx'
LOG_FILE = '/Users/yangjie/code/antigravity/log/debug.log'

def log_debug(message):
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception as e:
        print(f"Failed to log: {e}")

def main():
    print("开始整合功率数据...")
    log_debug("开始执行功率数据整合任务")
    
    files = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith('.xlsx')], key=lambda x: x)
    all_data = []
    
    for f in files:
        file_path = os.path.join(SOURCE_DIR, f)
        
        # Parse date from filename
        match = re.search(r'(\d{4}-\d{2}-\d{2})', f)
        if not match:
            print(f"Skipping file (no date found): {f}")
            continue
            
        date_str = match.group(1)
        
        # Check type
        is_new_energy = "新能源曲线" in f
        is_output_curve = "出力曲线" in f
        
        try:
            if is_new_energy:
                # Read "New Energy" files
                # Header seems to be on row 1 (0-indexed) based on inspection
                df = pd.read_excel(file_path, header=1)
                
                # Verify columns
                if '时刻' in df.columns and '电力(兆瓦)' in df.columns:
                    # Clean/Filter columns
                    df = df[['时刻', '电力(兆瓦)']].copy()
                    df.insert(0, '日期', date_str)
                    df['数据来源'] = '新能源曲线'
                    all_data.append(df)
                    print(f"已处理: {f} ({len(df)} rows)")
                else:
                    log_debug(f"文件结构不匹配: {f} - Columns: {df.columns.tolist()}")
                    
            elif is_output_curve:
                # Check if it actually has data
                # Based on previous inspection, these files often have no curve data in Sheet1
                # We will skip them but log it
                log_debug(f"跳过无曲线数据文件: {f}")
                print(f"Skipping output curve file (no data): {f}")
                
        except Exception as e:
            error_msg = f"处理文件出错 {f}: {str(e)}"
            print(error_msg)
            log_debug(error_msg)
            
    # Consolidate
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        
        # Sort
        final_df['日期'] = pd.to_datetime(final_df['日期'])
        final_df = final_df.sort_values(by=['日期', '时刻'])
        final_df['日期'] = final_df['日期'].dt.strftime('%Y-%m-%d') # Format back to string
        
        # Save
        final_df.to_excel(OUTPUT_FILE, index=False)
        success_msg = f"整合完成。共 {len(final_df)} 条数据。已保存至: {OUTPUT_FILE}"
        print(success_msg)
        log_debug(success_msg)
    else:
        warn_msg = "未提取到任何有效数据。"
        print(warn_msg)
        log_debug(warn_msg)

if __name__ == "__main__":
    main()
