#!/bin/bash

# --- 配置部分 (Configuration) ---

# 1. SSH 主机别名 (你的 ~/.ssh/config 中配置的名称)
REMOTE_HOST="racknerd"

# 2. 远程网站根目录 (aaPanel 默认通常在 /www/wwwroot/ 下)
# 请修改 "your_website_folder" 为你在 aaPanel 中创建的具体网站目录名
REMOTE_DIR="/www/wwwroot/energymonitor.109376.xyz"

# 3. 本地文件
LOCAL_FILE="index.html"

# ------------------------------

echo "🚀 开始部署到 $REMOTE_HOST ..."

# 检查文件是否存在
if [ ! -f "$LOCAL_FILE" ]; then
    echo "❌ 错误: 找不到本地文件 $LOCAL_FILE"
    exit 1
fi

# 执行上传 (scp)
echo "📂 正在上传 index.html..."
scp "index.html" "$REMOTE_HOST:$REMOTE_DIR/index.html"

echo "📂 正在上传 favicon.png..."
scp "favicon.png" "$REMOTE_HOST:$REMOTE_DIR/favicon.png"

if [ $? -eq 0 ]; then
    echo "✅ 部署成功!"
    echo "🌍 请访问你的网站进行验证。"
else
    echo "❌ 部署失败，请检查 SSH 连接或远程目录权限。"
fi
