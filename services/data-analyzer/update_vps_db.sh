#!/bin/zsh

# 强制同步本地数据库到 VPS
# 用途：当你确信本地的 backend/data.db 是最新的，并且想覆盖 VPS 上的数据时使用。
# 警告：这会丢失 VPS 上产生的新数据！

SSH_ALIAS="racknerd"
VPS_PATH="/root/apps/data-analyzer"

echo "⚠️  警告：此操作将用本地数据库【强制覆盖】VPS 上的数据库！"
echo "VPS 上的现有数据（包括场站和存单历史）将丢失。"
read -q "REPLY?确认要继续吗？(y/n) "
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "操作已取消。"
    exit 1
fi

echo "📦 正在上传 backend/data.db..."
scp backend/data.db $SSH_ALIAS:$VPS_PATH/backend/data.db

if [ $? -eq 0 ]; then
    echo "✅ 数据库上传成功！"
    echo "🔧 正在修复远程权限..."
    ssh $SSH_ALIAS "chmod 777 $VPS_PATH/backend/data.db"
    echo "🔄 正在重启服务以加载新数据..."
    ssh $SSH_ALIAS "cd $VPS_PATH && docker-compose restart"
    echo "🎉 完成！"
else
    echo "❌ 上传失败。"
fi
