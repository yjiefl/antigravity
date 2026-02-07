import os

file_path = "NB_T 31147-2018 风电场工程风能资源测量与评估技术规范.md"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1

# Find start
for i, line in enumerate(lines):
    if "**B.0.3**" in line and "测风塔安装质量检查表" in line:
        start_idx = i
        break

# Find end: Look for next section header or end of file
# From previous , we see "B.0.4" at line 475
for i, line in enumerate(lines[start_idx+1:], start=start_idx+1):
    if "**B.0.4**" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    print(f"Found block: lines {start_idx+1} to {end_idx+1}")
    
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
        "| 11 | 各通道数据是否正常 | |\n",
        "| 12 | 数据记录仪编号是否正确 | |\n",
        "| 13 | 数据卡是否插人，是否正常 | |\n",
        "| 14 | 时间设置是否正确 | |\n",
        "| 15 | 远程数据传输与在线监测是否正常 | |\n",
        "| 16 | 重置记录器的程序是否正常 | |\n",
        "| 17 | 加密措施是否有效 | |\n",
        "| 18 | 数据采集器是否上锁 | |\n",
        "| 19 | 数据采集器内是否附干燥剂 | |\n",
        "| **四** | **供电系统** | |\n",
        "| 20 | 电池是否正常 | |\n",
        "| 21 | 光伏系统是否正常 | |\n",
        "| **五** | **接地系统** | |\n",
        "| 22 | 塔体接地系统是否符合安装报告要求并连接正常 | |\n",
        "| 23 | 记录仪地线是否连接 | |\n",
        "| 24 | 接地线与避雷针是否连接 | |\n",
        "| 25 | 接地电阻复测结论 | |\n",
        "| **六** | **施工** | |\n",
        "| 26 | 测风塔基础是否满足安装报告要求 | |\n",
        "| 27 | 拉线地锚是否满足安装报告要求 | |\n",
        "| 28 | 施工废弃物是否清理 | |\n\n"
    ]
    
    final_lines = lines[:start_idx] + new_content + lines[end_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)
    
    print("Successfully replaced content.")

else:
    print(f"Could not find markers. Start: {start_idx}, End: {end_idx}")

