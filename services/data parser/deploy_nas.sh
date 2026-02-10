#!/bin/bash

# NAS 配置
NAS_USER="yjiefl"
NAS_IP="192.168.3.10"
NAS_PORT="22222"
NAS_PATH="services/power-analysis" 

echo "🚀 开始修复版 QNAP 部署流程..."

# 1. 准备本地文件压缩包
# 使用 ustar 格式以消除 QNAP 上的 extended header 警告
# 使用 COPYFILE_DISABLE 消除 ._ 文件
echo "📦 正在打包项目文件 (格式优化)..."
export COPYFILE_DISABLE=1
tar --format=ustar \
    --exclude='deploy_package.tar.gz' \
    --exclude='__pycache__' \
    --exclude='uploads/*' \
    --exclude='output/*' \
    --exclude='.git' \
    -czf deploy_package.tar.gz .

# 2. 在 NAS 上创建目录
echo "📂 在 QNAP 上确认目录结构..."
ssh -p $NAS_PORT $NAS_USER@$NAS_IP "mkdir -p ~/$NAS_PATH"

# 3. 上传文件
echo "📤 传输安装包中..."
scp -P $NAS_PORT deploy_package.tar.gz $NAS_USER@$NAS_IP:~/$NAS_PATH/

# 4. 在 QNAP 环境下解压并运行
echo "🐳 正在 QNAP 上触发镜像构建与启动..."
ssh -p $NAS_PORT $NAS_USER@$NAS_IP "
    cd ~/$NAS_PATH
    # 解压并通过 --no-same-owner 避免权限警告
    tar -xzf deploy_package.tar.gz
    rm deploy_package.tar.gz
    
    # 注入核心环境路径
    export PATH=\$PATH:/share/CACHEDEV1_DATA/.qpkg/container-station/bin:/usr/local/bin
    
    # 确定 Compose 命令
    if which docker-compose > /dev/null 2>&1; then
        COMPOSE_CMD=\"docker-compose\"
    else
        COMPOSE_CMD=\"docker compose\"
    fi
    
    echo \"正在使用镜像代理拉取并构建 (请耐心等待)...\"
    
    # 运行部署
    if \$COMPOSE_CMD up -d --build; then
        echo \"\"
        echo \"✨ [SUCCESS] 容器服务已在后端启动成功！\"
    else
        echo \"❌ [ERROR] 构建失败，依然存在网络问题。\"
        exit 1
    fi
"

# 5. 清理本地缓存
rm deploy_package.tar.gz

echo "✅ 流程结束！"
echo "您可以访问: http://$NAS_IP:5004"
echo "提示：如果访问依然出现 502 错误，请尝试在 NAS 上运行以下命令查看详细日志："
echo "ssh -p $NAS_PORT $NAS_USER@$NAS_IP 'cd ~/$NAS_PATH && docker compose logs'"

