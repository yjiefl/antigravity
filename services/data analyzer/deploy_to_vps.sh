#!/bin/zsh

# VPS 自动化部署脚本
# 修改人: Antigravity (AI)
# 日期: 2026-01-31

# --- 配置区 ---
SSH_ALIAS="racknerd" # 使用用户 ~/.ssh/config 中配置的别名
VPS_IP="107.174.62.30"
VPS_PATH="/root/apps/data-analyzer" # VPS 上的部署路径
# --- --- --- ---

echo "📡 正在检查 SSH 连接 ($SSH_ALIAS)..."
if ! ssh -q -o ConnectTimeout=5 $SSH_ALIAS exit; then
    echo "❌ 无法连接到 VPS，请检查 SSH 配置或网络。"
    exit 1
fi

echo "📡 准备同步代码到 VPS..."

# 确保远程目录存在
ssh $SSH_ALIAS "mkdir -p $VPS_PATH/backend $VPS_PATH/log $VPS_PATH/logs"

# 使用 rsync 进行增量同步
# --delete: 删除远程有但本地没有的文件
# --exclude: 排除不需要同步的文件
# ⚠️ 注意: 排除 data.db 以免覆盖生产环境数据
rsync -avz --delete --progress \
    --exclude "node_modules" \
    --exclude ".git" \
    --exclude ".DS_Store" \
    --exclude "frontend/dist" \
    --exclude "backend/data.db" \
    --exclude "log/" \
    --exclude "logs/" \
    ./ $SSH_ALIAS:$VPS_PATH

if [ $? -eq 0 ]; then
    echo "✅ 同步成功！"
    echo "🛠  正在远程触发 Docker 重建与启动..."
    
    # 通过 SSH 远程执行 docker-compose 命令
    # 使用 docker-compose 或 docker compose 取决于目标系统环境
    ssh $SSH_ALIAS "cd $VPS_PATH && (docker-compose up -d --build || docker compose up -d --build)"
    
    if [ $? -eq 0 ]; then
        echo "------------------------------------------------"
        echo "🚀 部署完成！"
        echo "🌐 系统访问地址: http://$VPS_IP:5003"
        echo "------------------------------------------------"
    else
        echo "❌ 远程 Docker 构建失败，请检查 VPS 是否已安装 docker 和 docker compose。"
    fi

    # 修复权限：确保 SQLite 数据库和日志目录可写
    echo "🔧 正在修复远程文件权限..."
    ssh $SSH_ALIAS "chmod -R 777 $VPS_PATH/backend $VPS_PATH/log $VPS_PATH/logs 2>/dev/null"
    
else
    echo "❌ 代码同步失败，请检查 rsync/ssh 状态。"
fi
