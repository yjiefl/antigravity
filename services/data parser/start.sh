#!/bin/bash

# 获取脚本所在目录的绝对路径
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "正在停止已运行的分析服务..."
# 查找正在运行 app.py 的进程并终止
pkill -f "python3 app.py" || echo "未发现正在运行的进程。"

# 运行环境检查
python3 check_env.py
if [ $? -ne 0 ]; then
    echo "❌ 环境检查未通过，启动中止。"
    exit 1
fi

echo "正在启动新能源功率预测数据分析服务..."

# 后台启动应用，并将日志输出到 server.log
nohup python3 app.py > server_v2.log 2>&1 &

# 等待 2 秒确保服务启动
sleep 2

echo "服务已启动！正在自动打开网页..."
echo "访问地址: http://127.0.0.1:5001"

# 在 macOS 上自动打开默认浏览器
open "http://127.0.0.1:5001"

echo "日志文件: $DIR/server_v2.log"
