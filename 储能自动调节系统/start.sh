#!/bin/bash

# 储能自动调节系统 - 启动脚本
# 功能：一键开启后端和前端服务

echo "🚀 正在启动储能自动调节系统..."

BASE_DIR="/Users/yangjie/code/antigravity/储能自动调节系统"

# 辅助函数：清理端口
cleanup_port() {
    local port=$1
    local name=$2
    local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
    if [ -n "$pid" ]; then
        echo "⚠️ 发现 $name 端口 $port 被占用 (PID: $pid)，正在清理..."
        kill -9 $pid
        sleep 1
    fi
}

# 1. 启动后端
echo "--- [1/2] 检查并启动后端服务 (FastAPI) ---"
cleanup_port 8000 "后端"
cd "$BASE_DIR/backend"
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$BASE_DIR/log/backend.log" 2>&1 &
echo "✅ 后端已在后台启动 (PID: $!)"

# 2. 启动前端
echo "--- [2/2] 检查并启动前端服务 (Vite) ---"
cleanup_port 5173 "前端"
cd "$BASE_DIR/frontend"
nohup npm run dev > "$BASE_DIR/log/frontend.log" 2>&1 &
echo "✅ 前端已在后台启动 (PID: $!)"

echo ""
echo "🎉 系统启动成功！"
echo "🌐 访问地址: http://localhost:5173"
echo "📜 日志路径: $BASE_DIR/log/"
