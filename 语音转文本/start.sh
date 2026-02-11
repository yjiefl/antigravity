#!/bin/bash

# 获取项目根目录的绝对路径
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "正在清理残留服务..."
# 关闭正在运行在 8000 (后端) 和 5173 (前端) 端口的进程
PORT_BACKEND=8000
PORT_FRONTEND=5173

for port in $PORT_BACKEND $PORT_FRONTEND; do
    pid=$(lsof -t -i:$port)
    if [ -n "$pid" ]; then
        echo "发现端口 $port 有残留进程 (PID: $pid)，正在关闭..."
        kill -9 $pid
    fi
done

echo "----------------------------------------"
echo "正在启动后端服务 (FastAPI)..."
cd "$PROJECT_ROOT/server"
# 检查后端依赖环境（可选：如果使用 venv 则激活）
# if [ -d "venv" ]; then source venv/bin/activate; fi

nohup python3 main.py > server.log 2>&1 &
echo "后端服务已启动，日志见 server/server.log"

echo "----------------------------------------"
echo "正在启动前端服务 (Vite)..."
cd "$PROJECT_ROOT/web"
# 确保 node_modules 存在
if [ ! -d "node_modules" ]; then
    echo "正在安装前端依赖..."
    npm install
fi

nohup npm run dev > web.log 2>&1 &
echo "前端服务已启动，日志见 web/web.log"

echo "========================================"
echo "服务启动过程已触发。请稍等片刻后访问 http://localhost:5173"
echo "========================================"
