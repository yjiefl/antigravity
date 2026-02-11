#!/bin/bash

echo "========================================"
echo "正在停止语音转文本服务..."
PORT_BACKEND=8000
PORT_FRONTEND=5173

stopped=false
for port in $PORT_BACKEND $PORT_FRONTEND; do
    pid=$(lsof -t -i:$port)
    if [ -n "$pid" ]; then
        echo "正在关闭端口 $port 的进程 (PID: $pid)..."
        kill -9 $pid
        stopped=true
    else
        echo "端口 $port 没有正在运行的服务。"
    fi
done

if [ "$stopped" = true ]; then
    echo "所有相关服务已停止。"
else
    echo "未发现运行中的服务。"
fi
echo "========================================"
