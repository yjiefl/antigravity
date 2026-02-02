#!/bin/bash

# 储能自动调节系统 - 停止脚本
# 功能：一键关闭后端和前端服务

echo "🛑 正在停止储能自动调节系统..."

# 停止后端 (uvicorn/python)
echo "--- 停止后端服务 (8000端口) ---"
BACKEND_PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
if [ -n "$BACKEND_PID" ]; then
    kill $BACKEND_PID
    echo "✅ 已停止后端进程 (PID: $BACKEND_PID)"
else
    echo "ℹ️ 后端服务未运行。"
fi

# 停止前端 (vite/node)
echo "--- 停止前端服务 (5173端口) ---"
FRONTEND_PID=$(lsof -Pi :5173 -sTCP:LISTEN -t)
if [ -n "$FRONTEND_PID" ]; then
    # 注意：vite 可能会启动子进程，有时需要 kill 集群
    kill $FRONTEND_PID
    echo "✅ 已停止前端进程 (PID: $FRONTEND_PID)"
else
    echo "ℹ️ 前端服务未运行。"
fi

echo ""
echo "🏁 系统已停止。"
