#!/bin/bash

# 获取项目根目录的绝对路径
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT_BACKEND=8000
PORT_FRONTEND=5005

echo "========================================"
echo "正在清理残留服务..."

# 优先通过 pids.txt 停止
if [ -f "$PROJECT_ROOT/pids.txt" ]; then
    while read pid; do
        if ps -p $pid > /dev/null; then
            echo "正在关闭残留进程 (PID: $pid)..."
            kill -9 $pid
        fi
    done < "$PROJECT_ROOT/pids.txt"
    rm "$PROJECT_ROOT/pids.txt"
fi

# 兜底清理端口
for port in $PORT_BACKEND $PORT_FRONTEND; do
    pids=$(lsof -t -i:$port)
    if [ -n "$pids" ]; then
        echo "发现端口 $port 有残留进程，正在关闭..."
        echo "$pids" | xargs kill -9
    fi
done

echo "----------------------------------------"
echo "正在启动后端服务 (FastAPI)..."
cd "$PROJECT_ROOT/server"

# 处理虚拟环境
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

# 安装依赖
echo "正在检查后端依赖..."
./venv/bin/pip install -r requirements.txt > /dev/null 2>&1

nohup ./venv/bin/python -u main.py > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!
echo "后端服务已启动 (PID: $BACKEND_PID)，日志见 backend.log"

echo "----------------------------------------"
echo "正在启动前端服务 (Vite)..."
cd "$PROJECT_ROOT/web"

# 确保 node_modules 存在
if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖..."
    npm install
fi

nohup npm run dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "前端服务已启动 (PID: $FRONTEND_PID)，日志见 frontend.log"

# 保存 PID
echo "$BACKEND_PID" > "$PROJECT_ROOT/pids.txt"
echo "$FRONTEND_PID" >> "$PROJECT_ROOT/pids.txt"

echo "========================================"
echo "服务启动过程已触发。"
echo "正在打开浏览器访问 http://localhost:$PORT_FRONTEND ..."
echo "========================================"

sleep 2 # 等待服务完全就绪
open "http://localhost:$PORT_FRONTEND"
