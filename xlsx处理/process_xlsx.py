
import openpyxl
import re
import csv
import os

def get_status(cell):
    """
    根据单元格背景色和内容判断组串状态
    1. 红色 (FFFF0000) -> 风灾未修复
    2. 黄色 (FFFFFF00) -> 零支路
    3. 为空 -> 空支路
    """
    fill = cell.fill
    if fill and fill.start_color:
        color = fill.start_color
        rgb = "None"
        if color.type == 'rgb':
            rgb = color.rgb
        elif color.type == 'theme':
            # Theme colors are tricky, but based on inspection we saw hex values
            # If it's a theme color, we might need more logic, 
            # but inspect showed FFFFFF00 and FFFF0000.
            pass
        
        if rgb == "FFFF0000":
            return "风灾未修复"
        if rgb == "FFFFFF00":
            return "零支路"
            
    if cell.value is None or str(cell.value).strip() == "":
        return "空支路"
    
    return "正常"

def parse_inverter_info(info_str):
    """
    解析 #箱变-逆变器 格式
    如: #1-1号逆变器 -> (1, 1)
    """
    if not info_str:
        return None, None
    match = re.search(r'#(\d+)-(\d+)', str(info_str))
    if match:
        return match.group(1), match.group(2)
    return "未知", "未知"

def process_excel(input_path, output_path):
    print(f"Loading {input_path}...")
    wb = openpyxl.load_workbook(input_path, data_only=True)
    sheet = wb.active
    
    results = []
    
    # 假设第一行为表头，从第二行开始处理
    # 列 4 到 27 为组串 1 到 24
    header = [cell.value for cell in sheet[1]]
    
    for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=False), start=2):
        collector_line = row[1].value # 集电线及方阵
        inverter_raw = row[2].value    # 逆变器正式编号
        
        if not collector_line and not inverter_raw:
            continue
            
        box_trans, inv_num = parse_inverter_info(inverter_raw)
        
        # 遍历组串列 (下标 3 到 26, 对应 D 到 AA)
        for col_idx in range(3, 27):
            cell = row[col_idx]
            string_num = col_idx - 2 # 组串号 1, 2, 3...
            
            status = get_status(cell)
            
            # 仅记录要求的异常/特定状态
            if status in ["风灾未修复", "零支路", "空支路"]:
                results.append({
                    "集电线路": collector_line,
                    "箱变号": box_trans,
                    "逆变器号": inv_num,
                    "组串号": string_num,
                    "组串状态": status
                })

    # 写入 CSV
    keys = ["集电线路", "箱变号", "逆变器号", "组串号", "组串状态"]
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(results)
    
    print(f"Processed {len(results)} rows. Saved to {output_path}")
    return results

if __name__ == "__main__":
    input_file = "/Users/yangjie/code/antigravity/xlsx处理/岑凡现场提供故障组串数据表.xlsx"
    output_file = "/Users/yangjie/code/antigravity/xlsx处理/岑凡故障组串标准表.csv"
    process_excel(input_file, output_file)
