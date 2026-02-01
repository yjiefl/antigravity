#!/bin/bash

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$( dirname "$SCRIPT_DIR" )"

cd "$PROJECT_DIR"

echo "🚀 正在启动 Chart Studio..."

# 检查 3000 端口是否被占用
PID=$(lsof -t -i:3000)
if [ ! -z "$PID" ]; then
    echo "⚠️  端口 3000 已被占用 (PID: $PID)，正在尝试清理..."
    kill -9 $PID
    sleep 1
fi

# 在后台启动服务
npx -y serve . -l 3000 > /dev/null 2>&1 &

# 等待一秒确保服务启动
sleep 1

echo "🌐 服务已在 http://localhost:3000 启动"
echo "🖥️  正在打开浏览器..."

open "http://localhost:3000"

echo "✅ 启动完成！"
