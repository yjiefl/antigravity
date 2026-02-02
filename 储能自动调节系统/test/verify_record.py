import pandas as pd
import numpy as np
from datetime import datetime

def check_logic(row, next_row, config):
    """
    验证单步调节是否符合逻辑
    """
    storage_power = float(row['储能出力（MW）'])
    dispatch_target = float(row['调度指令值（MW）'])
    pv_power = float(row['光伏出力（MW）'])
    charge_limit = float(row.get('充电功率上限（MW）', config['charge_limit']))
    discharge_limit = config['discharge_limit']
    soc = float(row['SOC（%）'])
    dead_zone = config['dead_zone']
    step_size = config['step_size']
    soc_min = config['soc_min']
    soc_max = config['soc_max']
    
    total_power = pv_power + storage_power
    deviation = dispatch_target - total_power
    
    # 1. 验证总有功计算
    if abs(total_power - float(row['总有功（MW）'])) > 0.05:
        return False, f"总有功计算错误: {pv_power} + {storage_power} != {row['总有功（MW）']}"
    
    # 2. 计算条件
    in_dead_zone = abs(deviation) <= dead_zone
    
    # 如果在死区，下一个储能出力应该接近当前出力（允许微小波动 0.1MW）
    next_storage_power = float(next_row['储能出力（MW）'])
    if in_dead_zone:
        if abs(next_storage_power - storage_power) > 0.1:
            # 检查是否因为调度指令变了或者光伏出力变了导致刚好落入死区，但上一刻的指令还没执行完？
            # 或者是在死区内不应该动。
            return False, f"在死区内 (|{deviation:.2f}| <= {dead_zone})，不应调节，但出力从 {storage_power} 变为 {next_storage_power}"
    else:
        # 不在死区，计算目标
        ideal_target = dispatch_target - pv_power
        
        # 应用约束
        constrained_ideal = ideal_target
        if constrained_ideal < charge_limit:
            constrained_ideal = charge_limit
        elif constrained_ideal > discharge_limit:
            constrained_ideal = discharge_limit
            
        if soc <= soc_min and constrained_ideal > 0:
            constrained_ideal = 0
        elif soc >= soc_max and constrained_ideal < 0:
            constrained_ideal = 0
            
        change = constrained_ideal - storage_power
        clamped_change = max(-step_size, min(step_size, change))
        expected_target = storage_power + clamped_change
        
        # 实际变化
        actual_change = next_storage_power - storage_power
        
        # 验证变化方向
        if clamped_change > 0 and actual_change < -0.1:
             return False, f"应该增加出力 (目标方向 {clamped_change:.2f})，实际却减少了 ({actual_change:.2f})"
        if clamped_change < 0 and actual_change > 0.1:
             return False, f"应该减少出力 (目标方向 {clamped_change:.2f})，实际却增加了 ({actual_change:.2f})"
             
        # 验证步长限制 (允许 0.2MW 的浮动误差)
        if abs(actual_change) > step_size + 0.2:
             # 有时候可能有很大的跳变，比如充电上限调整？
             # 检查是否是刚开始运行或者有特殊指令
             return False, f"调节步长超限: 实际变化 {abs(actual_change):.2f} > 步长 {step_size}"

    return True, "OK"

def main():
    try:
        # 读取CSV，处理制表符分隔
        df = pd.read_csv('/Users/yangjie/code/antigravity/储能自动调节系统/test/record.csv', sep='\t')
    except Exception as e:
        # 尝试逗号分隔
        df = pd.read_csv('/Users/yangjie/code/antigravity/储能自动调节系统/test/record.csv')
    
    # 清洗数据：去掉可能的空行或全NaN行
    df = df.dropna(how='all')
    
    config = {
        'dead_zone': 1.2,
        'step_size': 2.0,
        'soc_min': 8.0,
        'soc_max': 100.0,
        'charge_limit': -50.0,
        'discharge_limit': 50.0
    }
    
    errors = []
    for i in range(len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i+1]
        
        # 检查时间戳，如果间隔太长（比如超过 10 分钟），可能不是连续调节过程
        t1 = datetime.strptime(f"{row['日期']} {row['时间']}", "%Y/%m/%d %H:%M:%S")
        t2 = datetime.strptime(f"{next_row['日期']} {next_row['时间']}", "%Y/%m/%d %H:%M:%S")
        if (t2 - t1).total_seconds() > 600:
            continue
            
        success, msg = check_logic(row, next_row, config)
        if not success:
            errors.append({
                'index': i,
                'time': f"{row['日期']} {row['时间']}",
                'error': msg,
                'row_data': row.to_dict(),
                'next_storage': next_row['储能出力（MW）']
            })
            
    # 输出结果
    print(f"共检查 {len(df)} 条记录")
    if not errors:
        print("✅ 验证通过！所有调节步骤均符合逻辑。")
    else:
        print(f"❌ 发现 {len(errors)} 处逻辑异常：")
        for err in errors[:10]:  # 只显示前10个
            print(f"- [行 {err['index']}] {err['time']}: {err['error']}")
        if len(errors) > 10:
            print(f"... 以及其他 {len(errors) - 10} 处异常")

if __name__ == "__main__":
    main()
