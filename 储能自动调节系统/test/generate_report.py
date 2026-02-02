import pandas as pd
import numpy as np
from datetime import datetime
import json

def analyze_record(file_path):
    try:
        df = pd.read_csv(file_path, sep='\t')
    except:
        df = pd.read_csv(file_path)
    
    df = df.dropna(how='all')
    
    config = {
        'dead_zone': 1.2,
        'step_size': 2.0,
        'soc_min': 8.0,
        'soc_max': 100.0,
        'discharge_limit': 50.0
    }
    
    results = {
        'total_records': len(df),
        'computation_errors': [],
        'step_limit_violations': [],
        'dead_zone_violations': [],
        'direction_errors': [],
        'limit_violations': [],
        'soc_violations': []
    }
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        # 1. 验证计算一致性
        pv = float(row['光伏出力（MW）']) if not pd.isna(row['光伏出力（MW）']) else 0
        storage = float(row['储能出力（MW）']) if not pd.isna(row['储能出力（MW）']) else 0
        total = float(row['总有功（MW）']) if not pd.isna(row['总有功（MW）']) else 0
        
        if abs(pv + storage - total) > 0.1:
            results['computation_errors'].append({
                'index': i,
                'time': f"{row['日期']} {row['时间']}",
                'details': f"{pv} + {storage} = {pv+storage} != {total}"
            })
            
        if i == len(df) - 1:
            continue
            
        next_row = df.iloc[i+1]
        t1 = datetime.strptime(f"{row['日期']} {row['时间']}", "%Y/%m/%d %H:%M:%S")
        t2 = datetime.strptime(f"{next_row['日期']} {next_row['时间']}", "%Y/%m/%d %H:%M:%S")
        
        if (t2 - t1).total_seconds() > 600:
            continue
            
        disp = float(row['调度指令值（MW）'])
        c_limit = float(row.get('充电功率上限（MW）', -50.0))
        soc = float(row['SOC（%）'])
        
        deviation = disp - total
        in_dead_zone = abs(deviation) <= config['dead_zone']
        
        next_storage = float(next_row['储能出力（MW）']) if not pd.isna(next_row['储能出力（MW）']) else 0
        actual_change = next_storage - storage
        
        # 2. 验证死区
        if in_dead_zone and abs(actual_change) > 0.2:
            results['dead_zone_violations'].append({
                'index': i,
                'time': f"{row['日期']} {row['时间']}",
                'deviation': deviation,
                'change': actual_change
            })
            
        # 3. 验证方向和步长
        if not in_dead_zone:
            ideal_target = disp - pv
            # 简单约束
            constrained_ideal = max(c_limit, min(config['discharge_limit'], ideal_target))
            if soc <= config['soc_min'] and constrained_ideal > 0: constrained_ideal = 0
            if soc >= config['soc_max'] and constrained_ideal < 0: constrained_ideal = 0
            
            direction = 1 if constrained_ideal > storage else -1
            if constrained_ideal == storage: direction = 0
            
            # 方向检查
            if direction != 0:
                if (direction == 1 and actual_change < -0.1) or (direction == -1 and actual_change > 0.1):
                    results['direction_errors'].append({
                        'index': i,
                        'time': f"{row['日期']} {row['时间']}",
                        'expected_dir': "增加" if direction == 1 else "减少",
                        'actual_change': actual_change,
                        'ideal_target': ideal_target
                    })
            
            # 步长检查
            if abs(actual_change) > config['step_size'] + 0.5: # 宽松一点
                results['step_limit_violations'].append({
                    'index': i,
                    'time': f"{row['日期']} {row['时间']}",
                    'change': actual_change,
                    'limit': config['step_size']
                })

    return results

def generate_report(results, output_file=None):
    lines = []
    lines.append("# 储能自动调节系统 - 运行数据验证全量报告")
    lines.append(f"\n> 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"> 验证数据源: `record.csv` (共 {results['total_records']} 条记录)")
    
    lines.append(f"\n## 1. 验证结论")
    if len(results['step_limit_violations']) + len(results['direction_errors']) > results['total_records'] * 0.1:
        lines.append("❌ **不满足。** 运行数据中存在大量与系统设计逻辑不符的记录，逻辑一致性比例较低。")
    else:
        lines.append("✅ **基本满足。** 系统运行数据大致符合设计逻辑。")

    lines.append(f"\n## 2. 统计概要")
    lines.append(f"- **总记录数**: {results['total_records']}")
    lines.append(f"- **计算错误 (P_pv + P_es != P_total)**: {len(results['computation_errors'])}")
    lines.append(f"- **调节步长违规 (>2.0MW)**: {len(results['step_limit_violations'])}")
    lines.append(f"- **死区控制违规 (偏差 <1.2MW时调节)**: {len(results['dead_zone_violations'])}")
    lines.append(f"- **调节方向错误 (与缩小偏差背道而驰)**: {len(results['direction_errors'])}")
    
    lines.append(f"\n## 3. 问题清单 (Top 100)")
    
    if results['computation_errors']:
        lines.append(f"\n### 3.1 计算不一致")
        for err in results['computation_errors'][:20]:
            lines.append(f"- [行 {err['index']}] {err['time']}: {err['details']}")
            
    if results['step_limit_violations']:
        lines.append(f"\n### 3.2 调节步长超限 (限制: 2.0MW)")
        for err in results['step_limit_violations'][:50]:
            lines.append(f"- [行 {err['index']}] {err['time']}: 实际变化 **{err['change']:.2f} MW**")
            
    if results['direction_errors']:
        lines.append(f"\n### 3.3 调节方向异常")
        for err in results['direction_errors'][:50]:
            lines.append(f"- [行 {err['index']}] {err['time']}: 应{err['expected_dir']} (理想目标 {err['ideal_target']:.2f} MW)，实际变化 {err['actual_change']:.2f} MW")

    if results['dead_zone_violations']:
        lines.append(f"\n### 3.4 死区控制异常 (阈值: 1.2MW)")
        for err in results['dead_zone_violations'][:50]:
            lines.append(f"- [行 {err['index']}] {err['time']}: 偏差为 {err['deviation']:.2f} MW，不应调节，但实际变化 {err['change']:.2f} MW")

    content = "\n".join(lines)
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"完整报告已保存至: {output_file}")
    else:
        print(content)

if __name__ == "__main__":
    file_path = '/Users/yangjie/code/antigravity/储能自动调节系统/test/record.csv'
    report_path = '/Users/yangjie/code/antigravity/储能自动调节系统/test/validation_report.md'
    res = analyze_record(file_path)
    generate_report(res, output_file=report_path)
