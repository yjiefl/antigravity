#!/bin/bash

# ZeroTier Moon Deployment Script
# Author: Antigravity (Google DeepMind)
# Description: Automates the setup of a ZeroTier Moon server on a remote Linux VPS.

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
echo "      ZeroTier Moon Auto-Installer                "
echo "=================================================="

SSH_CMD=""

if [ -n "$1" ]; then
    SSH_CMD="$1"
else
    echo "请输入远程服务器的 SSH 连接参数 (例如: root@123.45.67.89 或 -p 2222 user@host)"
    echo "注意: 不需要输入 'ssh' 命令本身，只需输入参数部分。"
    read -p "SSH连接参数: " SSH_CMD
fi

# Strip 'ssh ' prefix if user typed it
SSH_CMD=${SSH_CMD#ssh }

if [ -z "$SSH_CMD" ]; then
    error "SSH 连接参数不能为空。"
fi

# Try to extract IP from SSH command for default suggestion
# Simple regex to find an IP address in the command string
DETECTED_IP=$(echo "$SSH_CMD" | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | head -n 1)

# 2. Input: Public IP
echo ""
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

# 3. Input: Port
read -p "Moon 端口 [$DEFAULT_PORT]: " MOON_PORT
MOON_PORT=${MOON_PORT:-$DEFAULT_PORT}

log "目标服务器: $SSH_CMD"
log "公网配置: $PUBLIC_IP/$MOON_PORT"
log "正在连接服务器进行检查..."

# Helper to run SSH commands
# Uses generic StrictHostKeyChecking=no to avoid prompts on new hosts
run_remote() {
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 $SSH_CMD "$1"
}

# 4. Check and Install ZeroTier
log "检查 ZeroTier 安装状态..."
if run_remote "command -v zerotier-cli >/dev/null 2>&1"; then
    log "ZeroTier 已安装。"
else
    log "ZeroTier 未安装，正在安装..."
    run_remote "curl -s https://install.zerotier.com | sudo bash" || error "ZeroTier 安装失败。"
fi

# 5. Fetch Identity and Initialize Moon
log "初始化 Moon 配置..."

# Generate moon.json template
# Using a subshell on remote to handle permissions and directory changes
# We work in a temporary directory to avoid clutter
REMOTE_WORK_DIR="/tmp/zerotier_moon_$TIMESTAMP"
run_remote "mkdir -p $REMOTE_WORK_DIR"

# Check if identity.public exists, if typically in /var/lib/zerotier-one/identity.public
# We need root privileges usually to read identity.public
log "读取身份信息并生成配置模板..."
run_remote "sudo zerotier-idtool initmoon /var/lib/zerotier-one/identity.public > $REMOTE_WORK_DIR/moon.json" || error "无法生成 moon.json，请检查远程服务器是否有权限读取 identity.public。"

# 6. Modify moon.json
# Using python if available for safer JSON editing, or fallback to sed
log "配置 stableEndpoints..."
STABLE_ENDPOINT="$PUBLIC_IP/$MOON_PORT"

# Simple sed approach since the file format from initmoon is predictable (minified or standard)
# We replace "stableEndpoints": [] with our endpoint
run_remote "sed -i 's|\"stableEndpoints\": \[\]|\"stableEndpoints\": [\"$STABLE_ENDPOINT\"]|g' $REMOTE_WORK_DIR/moon.json" || error "修改 moon.json 失败"

# 7. Generate Signed Moon File
log "生成签名 Moon 文件 (.moon)..."
run_remote "cd $REMOTE_WORK_DIR && zerotier-idtool genmoon moon.json" || error "生成 .moon 文件失败"

# Find the generated .moon file name
MOON_FILE_NAME=$(run_remote "ls $REMOTE_WORK_DIR/*.moon | xargs basename")
MOON_ID=$(echo "$MOON_FILE_NAME" | sed 's/\.moon//' | sed 's/^000000//')

if [ -z "$MOON_FILE_NAME" ]; then
    error "找不到生成的 .moon 文件。"
fi

log "生成成功: $MOON_FILE_NAME (Moon ID: $MOON_ID)"

# 8. Deploy Moon File on Server
log "在服务器上部署 Moon..."
MOONS_D_DIR="/var/lib/zerotier-one/moons.d"
run_remote "sudo mkdir -p $MOONS_D_DIR"
run_remote "sudo cp $REMOTE_WORK_DIR/$MOON_FILE_NAME $MOONS_D_DIR/"
log "重启 ZeroTier 服务..."
run_remote "sudo systemctl restart zerotier-one" || warn "重启服务失败，请手动检查 (systemctl restart zerotier-one)"

# 9. Download and Archive
LOCAL_OUTPUT_DIR="$OUTPUT_BASE_DIR/${TIMESTAMP}_${MOON_ID}"
mkdir -p "$LOCAL_OUTPUT_DIR"

log "下载 Moon 文件到本地备份..."
# Use scp to download. Note: We need to handle the SSH command structure properly for scp.
# If SSH_CMD contains flags like -p, scp syntax is different (scp -P port).
# To simplify, we'll try to use the raw SSH connection args if simple, but handling complex SSH_CMD in SCP is tricky.
# Alternative: Use 'cat' over ssh and redirect to local file.
ssh -o StrictHostKeyChecking=no $SSH_CMD "cat $REMOTE_WORK_DIR/$MOON_FILE_NAME" > "$LOCAL_OUTPUT_DIR/$MOON_FILE_NAME"

if [ -s "$LOCAL_OUTPUT_DIR/$MOON_FILE_NAME" ]; then
    log "文件已保存至: $LOCAL_OUTPUT_DIR/$MOON_FILE_NAME"
else
    error "下载文件失败 (文件为空)。"
fi

# Cleanup Remote
run_remote "rm -rf $REMOTE_WORK_DIR"

# 10. Summary and Instructions
echo ""
echo "=================================================="
echo "          Moon 部署完成！"
echo "=================================================="
echo "Moon ID: $MOON_ID"
echo "文件位置: $LOCAL_OUTPUT_DIR/$MOON_FILE_NAME"
echo ""
echo "客户端加入方法 (在其他节点执行):"
echo "Linux/Mac:"
echo "  zerotier-cli orbit $MOON_ID $MOON_ID"
echo ""
echo "或者手动放置 .moon 文件:"
echo "  将 $MOON_FILE_NAME 放入客户端的 moons.d 目录中"
echo "  - Linux: /var/lib/zerotier-one/moons.d/"
echo "  - Windows: C:\ProgramData\ZeroTier\One\moons.d\\"
echo "  - Mac: /Library/Application Support/ZeroTier/One/moons.d/"
echo "  然后重启 ZeroTier 服务。"
echo "=================================================="
