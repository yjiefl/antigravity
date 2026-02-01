#!/bin/bash

echo "🛑 正在停止 Chart Studio (端口 3000)..."

# 查找并杀死占用 3000 端口的进程
PID=$(lsof -t -i:3000)

if [ -z "$PID" ]; then
    echo "🤷 未发现正在运行的服务。"
else
    kill -9 $PID
    echo "✅ 服务已停止。"
fi
