
"""
可用功率计算逻辑验证脚本

验证内容：
1. 受限时段判定逻辑（风电全天，光伏 06:00-20:00）
2. 全天未受限时长不足是否跳过修正（风电 < 1.5h，光伏 < 1h）
"""

from datetime import datetime, timedelta

def verify_power_logic(station_type: str, time_points: list, restriction_flags: list) -> dict:
    """
    模拟逻辑验证函数
    
    Args:
        station_type: 'wind' 或 'pv' (光伏)
        time_points: 时间点列表 ["05:45", "06:00", ...]
        restriction_flags: 对应的限电标志位列表 [True, False, ...]
    
    Returns:
        dict: { 
            "total_restricted_hours": float, 
            "total_unrestricted_hours": float,
            "should_correct_curve": bool 
        }
    """
    total_restricted_minutes = 0
    total_unrestricted_minutes = 0
    
    # 假设每个时间点代表 15 分钟间隔
    INTERVAL_MINUTES = 15
    
    for time_str, is_restricted in zip(time_points, restriction_flags):
        hour = int(time_str.split(":")[0])
        minute = int(time_str.split(":")[1])
        
        # 1. 判定是否在受限考量范围内
        is_in_scope = True
        if station_type == 'pv':
            # 光伏仅考虑 06:00 - 20:00
            # 注意：边界包含 06:00，但不包含 20:00 (通常区间定义为 [Start, End))
            # 这里简化处理，假设 06:00 - 19:45 这些点都在范围内
            if hour < 6 or hour >= 20:
                is_in_scope = False
        
        if not is_in_scope:
            # 不在考量范围内，直接跳过 (既不算受限，也不算不受限，也就是不参与统计?)
            # 文档原文：“光伏仅考虑 06:00-20:00”
            # 这通常意味着：如果在 06:00-20:00 之外发生限电，忽略之。
            # 但“未受限时长”的统计是否包含全天？
            # 文档原文：“全天未限电时间不足...则不对全天曲线进行偏差修正”。
            # 这暗示我们关心的是“全天有效的不受限时长”。
            # 对于光伏，夜间本来就没有出力，所以“不受限”通常指有光照且未被调度限制的时段。
            # 因此，夜间（非 06:00-20:00）通常被视为“无效时段”或自然受限（无光）。
            # 逻辑推断：光伏的“未受限时长”仅统计 06:00-20:00 期间未被限制的时段。
            continue

        if is_restricted:
            total_restricted_minutes += INTERVAL_MINUTES
        else:
            total_unrestricted_minutes += INTERVAL_MINUTES

    total_unrestricted_hours = total_unrestricted_minutes / 60.0
    
    # 2. 判定是否满足最小修正时长
    threshold = 1.5 if station_type == 'wind' else 1.0
    should_correct = total_unrestricted_hours >= threshold
    
    return {
        "total_restricted_hours": total_restricted_minutes / 60.0,
        "total_unrestricted_hours": total_unrestricted_hours,
        "should_correct_curve": should_correct,
        "threshold": threshold
    }

def run_tests():
    print("=== 开始执行测试用例 ===\n")
    
    # Test Case 1: 光伏 - 全部在 06:00 前 (无效)
    # 输入: 05:00 - 05:45 全部不受限
    times = ["05:00", "05:15", "05:30", "05:45"]
    flags = [False, False, False, False]
    result = verify_power_logic('pv', times, flags)
    assert result['total_unrestricted_hours'] == 0, f"Case 1 Failed: Expected 0, Got {result['total_unrestricted_hours']}"
    print("✓ Case 1: PV 06:00 前忽略 (Pass)")

    # Test Case 2: 光伏 - 06:00 - 07:00 不受限 (1小时)
    # 输入: 06:00, 06:15, 06:30, 06:45 (4个点 = 1小时)
    times = ["06:00", "06:15", "06:30", "06:45"]
    flags = [False, False, False, False]
    result = verify_power_logic('pv', times, flags)
    assert result['total_unrestricted_hours'] == 1.0, f"Case 2 Failed: Expected 1.0, Got {result['total_unrestricted_hours']}"
    assert result['should_correct_curve'] == True, f"Case 2 Failed: Should correct (>= 1.0h)"
    print("✓ Case 2: PV 满足 1.0h (Pass)")
    
    # Test Case 3: 光伏 - 06:00 - 06:45 不受限 (0.75小时)
    times = ["06:00", "06:15", "06:30"]
    flags = [False, False, False]
    result = verify_power_logic('pv', times, flags)
    assert result['should_correct_curve'] == False, f"Case 3 Failed: Should NOT correct (< 1.0h)"
    print("✓ Case 3: PV 不足 1.0h (Pass)")

    # Test Case 4: 风电 - 02:00 - 03:30 不受限 (1.5小时) - 全天有效
    times = ["02:00", "02:15", "02:30", "02:45", "03:00", "03:15"]
    flags = [False, False, False, False, False, False]
    result = verify_power_logic('wind', times, flags)
    assert result['total_unrestricted_hours'] == 1.5, f"Case 4 Failed: Expected 1.5, Got {result['total_unrestricted_hours']}"
    assert result['should_correct_curve'] == True, f"Case 4 Failed: Should correct (>= 1.5h)"
    print("✓ Case 4: Wind 满足 1.5h (凌晨) (Pass)")
    
    # Test Case 5: 风电 - 1.25小时
    times = ["02:00", "02:15", "02:30", "02:45", "03:00"]
    flags = [False, False, False, False, False]
    result = verify_power_logic('wind', times, flags)
    assert result['should_correct_curve'] == False, f"Case 5 Failed: Should NOT correct (< 1.5h)"
    print("✓ Case 5: Wind 不足 1.5h (Pass)")

    print("\n=== 所有测试用例通过 ===")

if __name__ == "__main__":
    run_tests()
