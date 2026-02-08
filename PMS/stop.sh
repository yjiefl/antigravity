#!/bin/bash

# 计划管理系统 - 一键停止脚本
# 使用方法: ./stop.sh

# 获取脚本所在目录的绝对路径
BASEDIR=$(dirname "$0")
cd "$BASEDIR"

echo "---------------------------------------"
echo "🛑 正在停止 计划管理系统服务..."
echo "---------------------------------------"

# 1. 停止前端
echo "⚛️ [1/3] 正在停止前端进程 (Port 5173)..."
if [ -f .frontend.pid ]; then
    kill $(cat .frontend.pid) 2>/dev/null
    rm .frontend.pid
fi
lsof -ti:5173 | xargs kill -9 2>/dev/null

# 2. 停止后端
echo "🐍 [2/3] 正在停止后端进程 (Port 8000)..."
if [ -f .backend.pid ]; then
    kill $(cat .backend.pid) 2>/dev/null
    rm .backend.pid
fi
lsof -ti:8000 | xargs kill -9 2>/dev/null

# 3. 停止数据库容器 (可选)
# echo "📦 [3/3] 正在停止 Docker 容器..."
# docker-compose stop db redis

echo "---------------------------------------"
echo "✅ 已停止所有服务。"
echo "---------------------------------------"
