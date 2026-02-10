#!/bin/bash

echo "正在停止新能源功率预测数据分析服务..."
# 查找正在运行 app.py 的进程并终止
pkill -f "python3 app.py"

if [ $? -eq 0 ]; then
    echo "服务已成功停止。"
else
    echo "未发现正在运行的服务进程。"
fi
