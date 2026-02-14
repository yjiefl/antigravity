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
    while true; do
        echo ""
        echo "=========================================="
        echo "       ZeroTier Moon 管理菜单"
        echo "=========================================="
        echo "1) 安装 / 重置 Moon (覆盖安装)"
        echo "2) 查看当前 Moon 状态"
        echo "3) 修改 Moon 监听 IP (Endpoints)"
        echo "4) 移除 Moon 角色 (卸载 Moon)"
        echo "0) 退出"
        echo "=========================================="
        read -p "请选择操作 [1]: " MOON_IO
        MOON_IO=${MOON_IO:-1}

        # Sub-Function: Deploy/Update Moon
        deploy_update_moon() {
           local NEW_IPs="$1"
           
           # Generate moon.json from identity.public
           # We keep valid moon.json in /var/lib/zerotier-one/moon.json for future edits
           log "正在生成 Moon 配置..."
           
           # 1. Init Moon
           run_remote "cd /var/lib/zerotier-one && sudo zerotier-idtool initmoon identity.public > moon.json"
           
           # 2. Update Endpoints
           # Format IPs for JSON: "ip/port","ip/port"
           # If user provided multiple IPs separated by space/comma, format them.
           # Input: "1.1.1.1/9993 2.2.2.2/9993" -> Output: "1.1.1.1/9993","2.2.2.2/9993"
           
           # Replace spaces/commas with ","
           local JSON_IPS=$(echo "$NEW_IPs" | sed 's/[, ]\+/", "/g')
           JSON_IPS="\"$JSON_IPS\""
           
           log "应用 IP 配置: $JSON_IPS"
           run_remote "sudo sed -i 's|\"stableEndpoints\": \[\]|\"stableEndpoints\": [$JSON_IPS]|g' /var/lib/zerotier-one/moon.json"
           
           # 3. Gen Moon
           log "签署并在本地生成 .moon 文件..."
           run_remote "cd /var/lib/zerotier-one && sudo zerotier-idtool genmoon moon.json"
           
           # 4. Install
           MOON_FILE=$(run_remote "ls /var/lib/zerotier-one/*.moon | head -n 1 | xargs basename")
           MOON_ID=$(echo "$MOON_FILE" | sed 's/\.moon//' | sed 's/^000000//')
           
           run_remote "sudo mkdir -p /var/lib/zerotier-one/moons.d"
           run_remote "sudo cp /var/lib/zerotier-one/$MOON_FILE /var/lib/zerotier-one/moons.d/"
           
           log "重启 ZeroTier 服务..."
           run_remote "sudo systemctl restart zerotier-one"

           # 5. Download
           log "保存副本到本地 output..."
           local LOCAL_DIR="$OUTPUT_BASE_DIR/${TIMESTAMP}_${MOON_ID}"
           mkdir -p "$LOCAL_DIR"
           ssh -o StrictHostKeyChecking=no $SSH_CMD "cat /var/lib/zerotier-one/$MOON_FILE" > "$LOCAL_DIR/$MOON_FILE"
           
           echo "Moon ID: $MOON_ID"
           echo "客户端加入命令: zerotier-cli orbit $MOON_ID $MOON_ID"
        }

        case "$MOON_IO" in
            1)
                echo "请输入 Moon 服务器的公网 IP 地址 (可输入多个，用空格分隔)。"
                if [ -n "$DETECTED_IP" ]; then
                    read -p "公网 IP [$DETECTED_IP]: " PUBLIC_IP
                    PUBLIC_IP=${PUBLIC_IP:-$DETECTED_IP}
                else
                    read -p "公网 IP: " PUBLIC_IP
                fi
                if [ -z "$PUBLIC_IP" ]; then error "IP 不能为空"; fi
                
                # Check for port
                if [[ "$PUBLIC_IP" != *"/"* ]]; then
                    read -p "端口 [$DEFAULT_PORT]: " M_PORT
                    M_PORT=${M_PORT:-$DEFAULT_PORT}
                    # Add port to IPs if missing
                    # Handle multiple IPs
                    FINAL_IPS=""
                    for ip in $PUBLIC_IP; do
                        if [[ "$ip" != *"/"* ]]; then
                            FINAL_IPS="$FINAL_IPS $ip/$M_PORT"
                        else
                            FINAL_IPS="$FINAL_IPS $ip"
                        fi
                    done
                    PUBLIC_IP="$FINAL_IPS"
                fi
                
                deploy_update_moon "$PUBLIC_IP"
                break 
                ;;
            2)
                echo "--- 当前 Moon 状态 ---"
                log "获取 Moon 信息..."
                # Check if moon.json exists
                if run_remote "[ -f /var/lib/zerotier-one/moon.json ]"; then
                     run_remote "cat /var/lib/zerotier-one/moon.json | grep -A 5 \"stableEndpoints\""
                     run_remote "zerotier-cli info"
                else
                     echo "未检测到 Moon 配置文件 (moon.json)。此节点可能不是 Moon 或者是旧版本。"
                fi
                echo ""
                read -p "按回车键返回菜单..."
                ;;
            3)
                echo "--- 修改 Moon 监听 IP ---"
                # Check current
                 if ! run_remote "[ -f /var/lib/zerotier-one/moon.json ]"; then
                     warn "未找到现有配置，请先执行安装(1)。"
                     continue
                 fi
                 
                 echo "当前 IP 配置:"
                 run_remote "grep \"stableEndpoints\" /var/lib/zerotier-one/moon.json"
                 
                 echo ""
                 echo "请输入新的 IP 列表 (覆盖旧配置)。格式: IP/PORT (例如: 1.2.3.4/9993)"
                 read -p "新 IP 列表: " NEW_LIST
                 
                 if [ -z "$NEW_LIST" ]; then
                    warn "输入为空，取消操作。"
                 else
                    # Process IPs to ensure format
                    # Simple pass-through if user knows what they are doing, or add default port
                    deploy_update_moon "$NEW_LIST"
                    break
                 fi
                ;;
            4)
                 read -p "警告: 确定要移除 Moon 角色吗? 客户端将无法通过此 Moon 加速。 [y/N]: " CONFIRM
                 if [[ "$CONFIRM" == "y" || "$CONFIRM" == "Y" ]]; then
                     log "正在移除 Moon 配置..."
                     run_remote "sudo rm -f /var/lib/zerotier-one/moon.json"
                     run_remote "sudo rm -f /var/lib/zerotier-one/moons.d/*.moon"
                     run_remote "sudo systemctl restart zerotier-one"
                     log "Moon 角色已移除。"
                 else
                     log "操作取消。"
                 fi
                 read -p "按回车键返回菜单..."
                 ;;
            0)
                exit 0
                ;;
            *)
                echo "无效选项"
                ;;
        esac
    done

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
    echo "访问地址: http://$SERVER_IP:3000"
    echo "默认用户: admin"
    echo "默认密码: password"
    echo "注意: 请第一次登录后立即修改默认密码！"
    echo "      请确保防火墙放行 TCP 3000 端口。"
    echo "=================================================="

else
    error "无效的选项。"
fi
