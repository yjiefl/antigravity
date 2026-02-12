#!/bin/bash

<<<<<<< HEAD:数字化工具/语音转文本/stop.sh
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
=======
# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ -f "$DIR/pids.txt" ]; then
    while read pid; do
        if ps -p $pid > /dev/null; then
            echo "Killing process $pid"
            kill $pid
        else
            echo "Process $pid not found"
        fi
    done < "$DIR/pids.txt"
    rm "$DIR/pids.txt"
    echo "Services stopped."
else
    echo "No pids.txt found. Are services running?"
    # Fallback to kill by port if needed, but risky.
    # lsof -ti:8000 | xargs kill
fi
>>>>>>> b79d775 (feat: auto sync at 2026-02-11 17:49:21):语音转文本/stop.sh
