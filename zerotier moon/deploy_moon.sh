#!/bin/bash

# ZeroTier Moon Deployment Script
# Author: Antigravity (Google DeepMind)
# Description: Automates the setup of a ZeroTier Moon server OR Planet controller (ztncui) on a remote Linux VPS.

set -e

# Configuration
OUTPUT_BASE_DIR="output"
DEFAULT_PORT="9993"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Helper function for logging
log() {
    echo -e "[$(date +'%T')] $1"
}

error() {
    echo -e "[$(date +'%T')] \033[0;31mERROR: $1\033[0m" >&2
    exit 1
}

warn() {
    echo -e "[$(date +'%T')] \033[0;33mWARNING: $1\033[0m"
}

# Ensure local output directory exists
mkdir -p "$OUTPUT_BASE_DIR"

# 1. Input: SSH Remote Address
echo "=================================================="
echo "      ZeroTier Assistant (Moon / Planet)          "
echo "=================================================="

SSH_CMD=""

if [ -n "$1" ]; then
    SSH_CMD="$1"
else
    echo "请输入远程服务器的 SSH 连接参数 (例如: root@123.45.67.89 或 -p 2200 user@host)"
    echo "注意: 不需要输入 'ssh' 命令本身，只需输入参数部分。"
    read -p "SSH连接参数: " SSH_CMD
fi

# Strip 'ssh ' prefix if user typed it
SSH_CMD=${SSH_CMD#ssh }

if [ -z "$SSH_CMD" ]; then
    error "SSH 连接参数不能为空。"
fi

# Try to extract IP from SSH command for default suggestion
DETECTED_IP=$(echo "$SSH_CMD" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | head -n 1)

log "目标服务器: $SSH_CMD"
log "正在连接服务器进行检查..."

# Helper to run SSH commands
run_remote() {
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SSH_CMD "$1"
}

# Check connectivity
if ! run_remote "echo 'Connection Success' >/dev/null"; then
    error "无法连接到服务器 $SSH_CMD，请检查网络或 SSH 配置。"
fi

# 2. Check and Install ZeroTier (Common Step)
log "检查 ZeroTier 安装状态..."
if run_remote "command -v zerotier-cli >/dev/null 2>&1"; then
    log "ZeroTier 已安装。"
else
    log "ZeroTier 未安装，正在安装..."
    run_remote "curl -s https://install.zerotier.com | sudo bash" || error "ZeroTier 安装失败。"
fi

# 3. Select Mode
echo ""
echo "请选择要部署的服务类型:"
echo "1) ZeroTier Moon 服务器 (Moon)"
echo "2) ZeroTier Planet 控制面板 (ztncui - 仅支持 Debian/Ubuntu)"
read -p "请输入选项 [1]: " CHOICE
CHOICE=${CHOICE:-1}

# --- MODE 1: MOON DEPLOYMENT ---
if [ "$CHOICE" == "1" ]; then
    echo ""
    echo "--- 正在开始 Moon 部署流程 ---"
    
    echo "请输入 Moon 服务器的公网 IP 地址 (用于其它节点连接)。"
    if [ -n "$DETECTED_IP" ]; then
        read -p "公网 IP [$DETECTED_IP]: " PUBLIC_IP
        PUBLIC_IP=${PUBLIC_IP:-$DETECTED_IP}
    else
        read -p "公网 IP: " PUBLIC_IP
    fi

    if [ -z "$PUBLIC_IP" ]; then
        error "公网 IP 必须填写。"
    fi

    read -p "Moon 端口 [$DEFAULT_PORT]: " MOON_PORT
    MOON_PORT=${MOON_PORT:-$DEFAULT_PORT}

    log "公网配置: $PUBLIC_IP/$MOON_PORT"
    log "初始化 Moon 配置..."

    # Generate moon.json template
    REMOTE_WORK_DIR="/tmp/zerotier_moon_$TIMESTAMP"
    run_remote "mkdir -p $REMOTE_WORK_DIR"

    log "读取身份信息并生成配置模板..."
    run_remote "sudo zerotier-idtool initmoon /var/lib/zerotier-one/identity.public > $REMOTE_WORK_DIR/moon.json" || error "无法生成 moon.json (Permission denied? Check identity.public)"

    log "配置 stableEndpoints..."
    STABLE_ENDPOINT="$PUBLIC_IP/$MOON_PORT"

    # Modify moon.json
    run_remote "sed -i 's|\"stableEndpoints\": \[\]|\"stableEndpoints\": [\"$STABLE_ENDPOINT\"]|g' $REMOTE_WORK_DIR/moon.json" || error "修改 moon.json 失败"

    log "生成签名 Moon 文件 (.moon)..."
    run_remote "cd $REMOTE_WORK_DIR && zerotier-idtool genmoon moon.json" || error "生成 .moon 文件失败"

    # Find the generated .moon file name
    MOON_FILE_NAME=$(run_remote "ls $REMOTE_WORK_DIR/*.moon | xargs basename")
    MOON_ID=$(echo "$MOON_FILE_NAME" | sed 's/\.moon//' | sed 's/^000000//')

    if [ -z "$MOON_FILE_NAME" ]; then
        error "找不到生成的 .moon 文件。"
    fi

    log "生成成功: $MOON_FILE_NAME (Moon ID: $MOON_ID)"

    log "在服务器上部署 Moon..."
    MOONS_D_DIR="/var/lib/zerotier-one/moons.d"
    run_remote "sudo mkdir -p $MOONS_D_DIR"
    run_remote "sudo cp $REMOTE_WORK_DIR/$MOON_FILE_NAME $MOONS_D_DIR/"
    log "重启 ZeroTier 服务..."
    run_remote "sudo systemctl restart zerotier-one" || warn "重启服务失败"

    # Download and Archive
    LOCAL_OUTPUT_DIR="$OUTPUT_BASE_DIR/${TIMESTAMP}_${MOON_ID}"
    mkdir -p "$LOCAL_OUTPUT_DIR"

    log "下载 Moon 文件到本地备份..."
    ssh -o StrictHostKeyChecking=no $SSH_CMD "cat $REMOTE_WORK_DIR/$MOON_FILE_NAME" > "$LOCAL_OUTPUT_DIR/$MOON_FILE_NAME"

    if [ -s "$LOCAL_OUTPUT_DIR/$MOON_FILE_NAME" ]; then
        log "文件已保存至: $LOCAL_OUTPUT_DIR/$MOON_FILE_NAME"
    else
        error "下载文件失败 (文件为空)。"
    fi

    # Cleanup Remote
    run_remote "rm -rf $REMOTE_WORK_DIR"

    echo ""
    echo "=================================================="
    echo "          Moon 部署完成！"
    echo "=================================================="
    echo "Moon ID: $MOON_ID"
    echo "文件位置: $LOCAL_OUTPUT_DIR/$MOON_FILE_NAME"
    echo "客户端加入: zerotier-cli orbit $MOON_ID $MOON_ID"
    echo "=================================================="

# --- MODE 2: PLANET (ZTNCUI) DEPLOYMENT ---
elif [ "$CHOICE" == "2" ]; then
    echo ""
    echo "--- 正在开始 Planet (ztncui) 部署流程 ---"
    
    # Check OS compatibility (Debian/Ubuntu only roughly check)
    if ! run_remote "command -v dpkg >/dev/null"; then
        error "ztncui 部署目前仅支持 Debian/Ubuntu 系统 (依赖 dpkg)。"
    fi

    log "下载 ztncui 处理包..."
    ZTNCUI_DEB="ztncui_0.8.14_amd64.deb"
    ZTNCUI_URL="https://s3-us-west-1.amazonaws.com/key-networks/deb/ztncui/1/x86_64/$ZTNCUI_DEB"
    
    # Download on remote
    run_remote "curl -O $ZTNCUI_URL" || error "下载 ztncui 失败"
    
    log "安装 ztncui..."
    run_remote "sudo dpkg -i $ZTNCUI_DEB" || error "安装 ztncui 失败"
    
    log "配置环境变量..."
    # Using 'sh -c' with sudo to handle redirection to protected files
    # 1. Set ZT_TOKEN
    run_remote "sudo sh -c \"echo ZT_TOKEN=\\\`cat /var/lib/zerotier-one/authtoken.secret\\\` > /opt/key-networks/ztncui/.env\"" || error "配置 Token 失败"
    
    # 2. Set HTTP_ALL_INTERFACES
    run_remote "sudo sh -c \"echo HTTP_ALL_INTERFACES=yes >> /opt/key-networks/ztncui/.env\""
    
    # 3. Set NODE_ENV
    run_remote "sudo sh -c \"echo NODE_ENV=production >> /opt/key-networks/ztncui/.env\""
    
    # 4. Set HTTPS_PORT (Optional, defaults to 3443, usually we might want 3000 for http but ztncui is https by default on 3443)
    # The user didn't specify port config in their snippet, but defaults are usually 3000 (HTTP) or 3443 (HTTPS).
    # From the user snippet: nothing about port. We stick to user snippet.
    
    log "设置文件权限..."
    run_remote "sudo chmod 400 /opt/key-networks/ztncui/.env"
    run_remote "sudo chown ztncui:ztncui /opt/key-networks/ztncui/.env"
    
    log "启用并重启服务..."
    run_remote "sudo systemctl enable ztncui"
    run_remote "sudo systemctl restart ztncui" || error "启动 ztncui 服务失败"
    
    # Check status
    if run_remote "systemctl is-active ztncui >/dev/null"; then
        log "ztncui 服务运行正常。"
    else
        warn "ztncui 服务状态异常，请登录服务器检查: systemctl status ztncui"
    fi

    # Retrieve IP for display
    if [ -n "$DETECTED_IP" ]; then
        SERVER_IP="$DETECTED_IP"
    else
        # Try to guess
        SERVER_IP="<Server_IP>"
    fi

    echo ""
    echo "=================================================="
    echo "          Planet (ztncui) 部署完成！"
    echo "=================================================="
    echo "访问地址: https://$SERVER_IP:3443"
    echo "默认用户: admin"
    echo "默认密码: password"
    echo "注意: 请第一次登录后立即修改默认密码！"
    echo "      请确保防火墙放行 TCP 3443 端口。"
    echo "=================================================="

else
    error "无效的选项。"
fi
