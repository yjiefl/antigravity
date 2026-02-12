#!/bin/bash

# 获取项目根目录的绝对路径
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT_BACKEND=8000
PORT_FRONTEND=5005

echo "========================================"
echo "正在停止语音转文本服务..."

stopped=false

# 1. 优先使用 pids.txt 停止
if [ -f "$PROJECT_ROOT/pids.txt" ]; then
    while read pid; do
        if ps -p $pid > /dev/null; then
            echo "正在关闭进程 (PID: $pid)..."
            kill -9 $pid
            stopped=true
        else
            echo "进程 $pid 已不存在。"
        fi
    done < "$PROJECT_ROOT/pids.txt"
    rm "$PROJECT_ROOT/pids.txt"
fi

# 2. 兜底清理剩余端口
for port in $PORT_BACKEND $PORT_FRONTEND; do
    pids=$(lsof -t -i:$port)
    if [ -n "$pids" ]; then
        echo "正在清理端口 $port 的残留进程..."
        echo "$pids" | xargs kill -9
        stopped=true
    fi
done

if [ "$stopped" = true ]; then
    echo "所有相关服务已停止。"
else
    echo "未发现正在运行的服务。"
fi

echo "========================================"
