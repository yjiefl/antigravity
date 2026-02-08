#!/bin/zsh

echo "🛑 正在停止 DataCurve Analyzer..."

# 1. 停止 Vite
echo " stopping Vite on ports 5173, 5175..."
lsof -t -i:5173 -i:5175 | xargs kill -9 2>/dev/null || true

# 2. 停止 Backend
echo " stopping Backend on ports 3001, 3002..."
lsof -t -i:3001 -i:3002 | xargs kill -9 2>/dev/null || true

# 3. 如果是 Docker 部署
if command -v docker-compose &> /dev/null; then
    if [ -f "docker-compose.yml" ]; then
        echo " stopping Docker containers..."
        docker-compose down
    fi
fi

echo "✅ 系统已停止。"
