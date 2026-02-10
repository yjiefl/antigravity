import os

file_path = "NB_T 31147-2018 风电场工程风能资源测量与评估技术规范.md"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

# Find start: Table B.0.3 declaration
for i, line in enumerate(lines):
    if "**B.0.3**" in line and "测风塔安装质量检查表" in line:
        start_idx = i
        break

# Find end: Look for next section header or end of file
for i, line in enumerate(lines[start_idx+1:], start=start_idx+1):
    # This is tricky because the table is broken.
    # Let's look for "现场是否清理干净" which is the last item
    if "现场是否清理干净" in line:
        # Check next few lines for table end or next section
        end_idx = i + 5 # Give some buffer to catch the end of table
        break

if start_idx != -1 and end_idx != -1:
    print(f"Found block: lines {start_idx+1} to {end_idx+1}")
    
    # Verify content range
    # print("".join(lines[start_idx:end_idx]))
    
    new_content = [
        "**B.0.3** 测风塔安装质量检查表可按表 B.0.3 的规定编制。\n\n",
        "**表 B.0.3 测风塔安装质量检查表**\n\n",
        "| 序号 | 内容 | 结论 |\n",
        "| :--- | :--- | :--- |\n",
        "| **一** | **塔架** | |\n",
        "| 1 | 塔体材料及尺寸是否满足安装报告要求 | |\n",
        "| 2 | 塔体是否垂直 | |\n",
        "| 3 | 拉线是否张紧 | |\n",
        "| 4 | 拉线方向是否满足安装报告要求 | |\n",
        "| 5 | 水平支臂与塔体连接是否正常 | |\n",
        "| **二** | **传感器** | |\n",
        "| 6 | 风速、风向传感器水平支臂安装方向是否满足安装报告要求 | |\n",
        "| 7 | 风速、风向传感器水平支臂长度是否满足安装报告要求 | |\n",
        "| 8 | 垂直支杆是否垂直 | |\n",
        "| 9 | 垂直支杆长度是否满足安装报告要求 | |\n",
        "| **三** | **记录传输设备** | |\n",
        "| 10 | 传感器电缆是否连接牢固 | |\n",
        "| 11 | 数据记录仪编号是否正确 | |\n",
        "| 12 | 数据卡是否插人，是否正常 | |\n",
        "| 13 | 时间设置是否正确 | |\n",
        "| 14 | 记录仪及终端各端口是否密封 | |\n",
        "| 15 | 太阳能板朝向是否正确，是否固定牢固 | |\n",
        "| 16 | 电源电压是否正常 | |\n",
        "| 17 | 接地与避雷与安装报告是否一致 | |\n",
        "| 18 | 信号是否良好 | |\n",
        "| **四** | **其他** | |\n",
        "| 19 | 现场是否清理干净 | |\n\n"
    ]
    
    # We need to be careful not to overwrite too much or too little.
    # The end_idx might be approximate.
    # Let's read until we find the next Section or clear text.
    # Actually, let's just use replace_file_content with exact context from reading first.
    pass
else:
    print(f"Could not find markers. Start: {start_idx}, End: {end_idx}")

