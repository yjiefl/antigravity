def calculate_pr(generation_kwh, capacity_mw, irradiation_kwh_m2):
    """
    计算光伏系统效率 (Performance Ratio)
    
    Args:
        generation_kwh: 发电量 (kWh)
        capacity_mw: 装机容量 (MW)
        irradiation_kwh_m2: 面板累计辐照量 (kWh/m2)
    
    Returns:
        float: PR值 (百分比)
    """
    if irradiation_kwh_m2 <= 0 or capacity_mw <= 0:
        return 0.0
    
    # 理论发电量 = 容量 * 峰值日照时数
    # 峰值日照时数 = 辐照量 (kWh/m2) / 1 (kW/m2)
    theoretical_generation = capacity_mw * 1000 * irradiation_kwh_m2
    
    pr = (generation_kwh / theoretical_generation) * 100
    return round(pr, 2)

if __name__ == "__main__":
    # Test
    print(f"PR Test: {calculate_pr(150000, 100, 2)}")
