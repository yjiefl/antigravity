#!/bin/bash

# --- 🚀 配置部分 (Configuration) ---

# 1. SSH 主机别名 (你的 ~/.ssh/config 中配置的名称)
REMOTE_HOST="racknerd"

# 2. 远程网站根目录 (aaPanel 默认通常在 /www/wwwroot/ 下)
# ⚠️ 注意：这会覆盖该目录下的同名文件，请确保目录正确！
REMOTE_DIR="/www/wwwroot/energymonitor.109376.xyz"

# 3. 本地项目目录
PROJECT_DIR="mobile"
DIST_DIR="$PROJECT_DIR/dist"

# ------------------------------

echo "========================================"
echo "   🚀 新能源监控系统(Mobile) 部署脚本   "
echo "========================================"

# 1. 检查并构建项目
echo ""
echo "🛠️  [1/3] 正在构建项目 (npm run build)..."

if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 找不到项目目录 '$PROJECT_DIR'，请确认你在正确的目录下运行脚本。"
    exit 1
fi

cd "$PROJECT_DIR" || exit

# 安装依赖 (可选，防止新拉取的代码没依赖)
# npm install 

# 运行构建
npm run build

if [ $? -ne 0 ]; then
    echo "❌ 构建失败！请检查错误日志。"
    exit 1
fi

cd ..
echo "✅ 构建完成！"

# 2. 检查构建产物
if [ ! -d "$DIST_DIR" ]; then
    echo "❌ 错误: 找不到构建输出目录 '$DIST_DIR'"
    exit 1
fi

# 3. 上传到服务器
echo ""
echo "📤 [2/3] 正在上传文件到 $REMOTE_HOST ..."
echo "    目标: $REMOTE_DIR"

# 使用 scp -r 递归上传 dist 下的所有内容
# 注意：通配符 * 会由本地 Shell 展开
scp -r "$DIST_DIR"/* "$REMOTE_HOST:$REMOTE_DIR/"

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 [3/3] 部署成功！"
    echo "🌍 访问地址: http://energymonitor.109376.xyz (请确保域名解析正确)"
    echo "========================================"
else
    echo ""
    echo "❌ 部署失败，请检查 SSH 连接或远程目录权限。"
fi
