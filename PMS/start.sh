#!/bin/bash

# 计划管理系统 - 一键启动脚本
# 使用方法: ./start.sh

# 获取脚本所在目录的绝对路径
BASEDIR=$(dirname "$0")
cd "$BASEDIR"

# 创建日志目录
mkdir -p log

# 0. 自动停止旧服务 (确保环境干净)
if [ -f "./stop.sh" ]; then
    echo "🧹 正在清理旧的服务进程..."
    bash ./stop.sh > /dev/null 2>&1
fi

echo "---------------------------------------"
echo "🚀 正在启动 PMS (Plan Master)..."
echo "---------------------------------------"

# 1. 启动 Docker 容器 (数据库 & Redis)
echo "📦 [1/4] 启动 Docker 数据库服务..."

# 检查并安装 Homebrew (macOS 必备)
if ! command -v brew &> /dev/null; then
    echo "🔍 未检测到 Homebrew，正在尝试安装..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# 检查 docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "🚚 正在通过 Homebrew 安装 Docker Desktop..."
    brew install --cask docker
fi

# 检查 Docker 守护进程是否正在运行，若未运行则尝试启动
if ! docker info &> /dev/null; then
    echo "🚀 正在启动 Docker 应用程序，请稍候..."
    open -a Docker
    # 等待 Docker 启动完成
    echo "⏳ 等待 Docker 引擎就绪..."
    while ! docker info &> /dev/null; do
        sleep 2
        echo -n "."
    done
    echo " ✅ Docker 已就绪"
fi

# 尝试使用 docker compose (V2) 或 docker-compose (V1)
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
else
    echo "🔧 正在安装缺失的 Docker Compose 插件..."
    brew install docker-compose
    # 再次确认
    if docker-compose version &> /dev/null; then
        DOCKER_COMPOSE_CMD="docker-compose"
    else
        echo "❌ 自动安装失败，请手动运行: brew install docker-compose"
        exit 1
    fi
fi

echo "⚙️ 使用命令: $DOCKER_COMPOSE_CMD"
$DOCKER_COMPOSE_CMD up -d db redis
if [ $? -ne 0 ]; then
    echo "❌ Docker 容器启动失败。请确保 Docker Desktop 已启动并检查 docker-compose.yml 配置。"
    exit 1
fi

# 等待数据库端口就绪
echo "⏳ 等待数据库端口 (5432) 响应..."
MAX_RETRIES=30
COUNT=0
while ! nc -z localhost 5432 > /dev/null 2>&1; do
    sleep 1
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
        echo "❌ 错误: 数据库启动超时，请检查 Docker 日志。"
        exit 1
    fi
done

# 2. 启动后端服务
echo "🐍 [2/4] 启动后端 FastAPI (端口 8000)..."

# 设置本地运行的环境变量，使用 asyncpg 异步驱动
export DATABASE_URL="postgresql+asyncpg://pms:pms_secret_2026@localhost:5432/plan_management"
export REDIS_URL="redis://localhost:6379/0"

cd backend
# 检查是否已有进程占用端口
if [ ! -d "venv" ]; then
    echo "📦 正在创建虚拟环境..."
    python3 -m venv venv
fi
source venv/bin/activate

echo "📦 检查并更新后端依赖..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null
# 针对 Mac M3 确保安装关键驱动和异步支持库
pip install asyncpg psycopg2-binary greenlet > /dev/null

# 自动初始化数据库表
if [ -f "init_db.py" ]; then
    echo "🗄️ 正在初始化数据库表..."
    # 增加重试机制，确保数据库内部完全就绪
    PYTHONPATH=. ./venv/bin/python3 init_db.py || (sleep 2 && PYTHONPATH=. ./venv/bin/python3 init_db.py)
fi
lsof -ti:8000 | xargs kill -9 2>/dev/null 
PYTHONPATH=. uvicorn app.main:app --reload --port 8000 > ../log/backend.log 2>&1 &
echo $! > ../.backend.pid
cd ..

# 3. 启动前端服务
echo "⚛️ [3/4] 启动前端 Vite (端口 5173)..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装前端依赖 (npm install)..."
    npm install
fi
lsof -ti:5173 | xargs kill -9 2>/dev/null
npm run dev > ../log/frontend.log 2>&1 &
echo $! > ../.frontend.pid
cd ..

# 4. 等待就绪并打开浏览器
echo "⏳ [4/4] 等待前端服务 (5173) 就绪..."
COUNT=0
while ! lsof -i:5173 > /dev/null 2>&1; do
    sleep 1
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge 20 ]; then
        echo "⚠️ 前端启动较慢，请稍后手动访问。"
        break
    fi
done

# 尝试打开浏览器 (macOS)
if command -v open > /dev/null; then
    open http://localhost:5173
fi

# 获取局域网 IP
LOCAL_IP=$(ipconfig getifaddr en0 || ipconfig getifaddr en1 || echo "127.0.0.1")

echo "---------------------------------------"
echo "✅ 启动完成！"
echo "---------------------------------------"
echo "🌐 本地访问: http://localhost:5173"
echo "📱 手机访问: http://$LOCAL_IP:5173"
echo "📄 后端 API: http://localhost:8000/api/docs"
echo "📝 日志收集: ./log/ (查看调试日志)"
echo "🛑 停止服务: 运行 ./stop.sh"
echo "---------------------------------------"
