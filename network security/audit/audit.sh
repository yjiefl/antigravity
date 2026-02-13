#!/bin/bash

# ==============================================================================
# 脚本名称: audit.sh
# 描述: Linux 安全审计脚本 (支持 Ubuntu/CentOS/Debian/Alinux)
# 功能: 安全检查、报告生成、交互式修复
# 作者: AntiGravity
# 版本: 1.2.1
# 日期: 2026-02-13
# ==============================================================================

# ---------------------- 基础配置 ----------------------
REPORT_FILE="./security_audit_report.md"
TMP_FAIL="/tmp/audit_fail.tmp"
TMP_PASS="/tmp/audit_pass.tmp"
TMP_INFO="/tmp/audit_info.tmp"
TMP_FAIL_IDS="/tmp/audit_fail_ids.txt" # 用于存储失败项的ID以供修复使用

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

# 全局变量
OS_TYPE=""
OS_VERSION=""
MODE="audit" # audit 或 fix

# ---------------------- 辅助函数 ----------------------

# 0. 检查 Root 权限
check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[!] 请使用 sudo 或 root 权限运行此脚本${NC}"
        exit 1
    fi
}

# 1. OS 检测
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_TYPE=$ID
        OS_VERSION=$VERSION_ID
        echo -e "${GREEN}[*] 检测到系统: $NAME ($VERSION)${NC}"
    else
        echo -e "${YELLOW}[!] 无法检测操作系统版本，默认按通用 Linux 处理${NC}"
        OS_TYPE="generic"
    fi
}

# 2. 初始化
init_audit() {
    > "$TMP_FAIL"
    > "$TMP_PASS"
    > "$TMP_INFO"
    > "$TMP_FAIL_IDS"
}

# 3. 记录结果
# 参数: $1=检查项ID(用于修复映射), $2=显示名称, $3=状态, $4=风险等级, $5=建议
log_result() {
    local id="$1"
    local item="$2"
    local status="$3"
    local risk="$4"
    local recommendation="$5"
    
    # 清理 markdown 特殊字符
    local d_item="${item//|/\\|}"
    local d_status="${status//|/\\|}"
    local d_recommendation="${recommendation//|/\\|}"
    
    local row="| $d_item | $d_status | $risk | $d_recommendation |"

    if [[ "$risk" == "High" ]] || [[ "$risk" == "Medium" ]]; then
        echo "$row" >> "$TMP_FAIL"
        echo "${id}|${item}" >> "$TMP_FAIL_IDS"
    elif [[ "$risk" == "Low" ]]; then
        echo "$row" >> "$TMP_PASS"
    else
        echo "$row" >> "$TMP_INFO"
    fi
}

# ---------------------- 审计功能模块 ----------------------

# [FS-01] 账号安全
audit_account() {
    echo "正在审计账号安全..."
    
    # Root 锁定
    local root_status=$(passwd -S root 2>/dev/null | awk '{print $2}')
    # CentOS passwd -S 格式不同 (通常是 LK 或 PS), Ubuntu 是 L/NP/P
    if [[ "$OS_TYPE" == "centos" ]] || [[ "$OS_TYPE" == "rhel" ]] || [[ "$OS_TYPE" == "alinux" ]]; then
        # CentOS: LK=Locked, PS=Password Set, NP=No Password
        if [[ "$root_status" == "LK" ]]; then root_status="L"; fi
    fi

    if [[ "$root_status" == "L" ]] || [[ "$root_status" == "NP" ]]; then
        log_result "ROOT_LOCK" "Root 账户锁定" "已锁定" "Low" "-"
    else
        log_result "ROOT_LOCK" "Root 账户锁定" "未锁定" "High" "锁定 Root，使用 sudo"
    fi

    # 空口令
    local empty_pw=$(awk -F: '($2 == "") {print $1}' /etc/shadow)
    if [[ -z "$empty_pw" ]]; then
        log_result "EMPTY_PW" "空口令用户" "无" "Low" "-"
    else
        log_result "EMPTY_PW" "空口令用户" "发现: $empty_pw" "High" "设置密码或锁定"
    fi

    # Uid 0
    local uid0=$(awk -F: '($3 == 0) {print $1}' /etc/passwd)
    if [[ "$uid0" == "root" ]]; then
        log_result "UID0_CHECK" "UID 0 用户检查" "无异常" "Low" "-"
    else
        log_result "UID0_CHECK" "UID 0 用户检查" "异常: $uid0" "High" "核查非 Root 的 UID 0 用户"
    fi
    
    # PAM Faillock
    local pam_file="/etc/pam.d/common-auth"
    if [[ "$OS_TYPE" == "centos" ]] || [[ "$OS_TYPE" == "rhel" ]] || [[ "$OS_TYPE" == "alinux" ]]; then
        pam_file="/etc/pam.d/system-auth"
    fi
    
    if grep -E "pam_faillock.so|pam_tally2.so" "$pam_file" >/dev/null 2>&1; then
        log_result "PAM_LOCK" "登录失败锁定" "已配置" "Low" "-"
    else
        log_result "PAM_LOCK" "登录失败锁定" "未配置" "Medium" "配置 pam_faillock/tally2"
    fi
}

# [NET-01] 网络安全
# [NET-01] 网络安全
audit_network() {
    echo "正在审计网络安全..."
    
    # 防火墙 (适配 UFW 和 firewalld)
    local fw_status="未运行"
    local fw_risk="High"
    
    if command -v ufw >/dev/null 2>&1; then
        local u_stat=$(ufw status | grep "Status" | awk '{print $2}')
        if [[ "$u_stat" == "active" ]]; then fw_status="UFW 激活"; fw_risk="Low"; fi
    elif command -v firewall-cmd >/dev/null 2>&1; then
        local f_stat=$(systemctl is-active firewalld)
        if [[ "$f_stat" == "active" ]]; then fw_status="Firewalld 激活"; fw_risk="Low"; fi
    fi
    
    log_result "FIREWALL" "防火墙状态" "$fw_status" "$fw_risk" "启用防火墙 (UFW/Firewalld)"

    # SSH 配置
    local sshd_conf="/etc/ssh/sshd_config"
    if [ -f "$sshd_conf" ]; then
        # Root Login
        local prl=$(grep "^PermitRootLogin" $sshd_conf | awk '{print $2}')
        if [[ "$prl" == "no" ]] || [[ "$prl" == "prohibit-password" ]]; then
            log_result "SSH_ROOT" "SSH Root 登录" "$prl" "Low" "-"
        else
            log_result "SSH_ROOT" "SSH Root 登录" "${prl:-yes}" "Medium" "设置为 no 或 prohibit-password"
        fi
        
        # Password Authentication
        local pass_auth=$(grep "^PasswordAuthentication" $sshd_conf | awk '{print $2}')
        if [[ "$pass_auth" == "no" ]]; then
            log_result "SSH_PASS" "SSH 密码认证" "禁止" "Low" "-"
        else
            log_result "SSH_PASS" "SSH 密码认证" "${pass_auth:-默认}" "Medium" "建议使用密钥，关闭密码认证"
        fi

        # MaxAuthTries
        local mat=$(grep "^MaxAuthTries" $sshd_conf | awk '{print $2}')
        if [[ -n "$mat" ]] && [[ "$mat" -le 4 ]]; then
            log_result "SSH_TRIES" "SSH 重试次数" "$mat" "Low" "-"
        else
            log_result "SSH_TRIES" "SSH 重试次数" "${mat:-默认}" "Medium" "设置 MaxAuthTries <= 4"
        fi
    else
        log_result "SSH_CONF" "SSH 配置文件" "未找到" "Medium" "检查配置位置"
    fi
    
    # 监听端口
    local func_ls=""
    if command -v ss >/dev/null; then func_ls="ss -tuln"; else func_ls="netstat -tuln"; fi
    local listen_ports=$($func_ls | grep LISTEN | awk '{print $5}' | cut -d: -f2 | sort -u | tr '\n' ' ')
    log_result "PORTS" "监听端口" "$listen_ports" "Info" "人工确认业务端口"
}

# [SYS-01] 系统配置
audit_system() {
    echo "正在审计系统配置..."
    
    # IP Forward
    local ipf=$(sysctl net.ipv4.ip_forward 2>/dev/null | awk '{print $3}')
    if [[ "$ipf" == "0" ]]; then
        log_result "IP_FWD" "IP 转发" "关闭" "Low" "-"
    else
        log_result "IP_FWD" "IP 转发" "开启" "Medium" "非路由需关闭"
    fi
    
    # ICMP Redirects
    local icmp_red=$(sysctl net.ipv4.conf.all.accept_redirects 2>/dev/null | awk '{print $3}')
    if [[ "$icmp_red" == "0" ]]; then
        log_result "ICMP_RED" "ICMP 重定向" "禁止" "Low" "-"
    else
        log_result "ICMP_RED" "ICMP 重定向" "允许" "Medium" "建议禁止接受重定向"
    fi
    
    # Rsyslog
    if systemctl is-active --quiet rsyslog; then
        log_result "RSYSLOG" "Rsyslog 服务" "运行中" "Low" "-"
    else
        log_result "RSYSLOG" "Rsyslog 服务" "未运行" "Medium" "启用 rsyslog"
    fi
    
    # Auditd
    if systemctl is-active --quiet auditd; then
        log_result "AUDITD" "Auditd 服务" "运行中" "Low" "-"
    else
        log_result "AUDITD" "Auditd 服务" "未运行" "Medium" "建议安装并启用 auditd"
    fi
    
    # Logrotate
    if [ -f "/etc/logrotate.conf" ]; then
        log_result "LOGROTATE" "Logrotate" "配置存在" "Low" "-"
    else
        log_result "LOGROTATE" "Logrotate" "缺失" "High" "配置日志轮转"
    fi
}

# [FS-02] 文件权限
audit_files() {
    echo "正在审计文件权限..."
    
    local shadow_perm=$(stat -c "%a" /etc/shadow 2>/dev/null)
    if [[ "$shadow_perm" -le 640 ]]; then
         log_result "PERM_SHADOW" "/etc/shadow 权限" "$shadow_perm" "Low" "-"
    else
         log_result "PERM_SHADOW" "/etc/shadow 权限" "$shadow_perm" "High" "设置为 640/600/400"
    fi
    
    local passwd_perm=$(stat -c "%a" /etc/passwd 2>/dev/null)
    if [[ "$passwd_perm" == "644" ]]; then
        log_result "PERM_PASSWD" "/etc/passwd 权限" "644" "Low" "-"
    else
        log_result "PERM_PASSWD" "/etc/passwd 权限" "$passwd_perm" "Medium" "建议 644"
    fi
    
    # Sudoers NOPASSWD check
    if grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ > /dev/null 2>&1; then
        log_result "SUDO_NOPASS" "Sudo NOPASSWD" "存在" "Medium" "建议移除免密 sudo"
    else
        log_result "SUDO_NOPASS" "Sudo NOPASSWD" "无" "Low" "-"
    fi
}

# [HOST-01] 主机信息
audit_host_info() {
    echo "正在收集主机信息..."
    local kernel=$(uname -r)
    log_result "INFO_KERNEL" "内核版本" "$kernel" "Info" "-"
    
    local uptime=$(uptime -p)
    log_result "INFO_UPTIME" "运行时间" "$uptime" "Info" "-"
    
    local cpu=$(grep -c processor /proc/cpuinfo)
    local mem=$(free -h | grep Mem | awk '{print $2}')
    log_result "INFO_SPEC" "规格" "${cpu}核 / ${mem}内存" "Info" "-"
    
    local disk=$(df -h / | tail -1 | awk '{print $5}')
    log_result "INFO_DISK" "根分区使用率" "$disk" "Info" ">80% 需关注"
}

# ---------------------- 修复功能模块 ----------------------

do_fix() {
    local fix_id="$1"
    echo -e "${YELLOW}[FIX] 正在修复项目: $fix_id ...${NC}"
    
    case "$fix_id" in
    "ROOT_LOCK")
        passwd -l root
        echo "已执行: passwd -l root"
        ;;
    "PAM_LOCK")
        echo -e "${RED}[!] PAM 配置较为复杂，建议手动修改。${NC}"
        ;;
    "FIREWALL")
        if [[ "$OS_TYPE" == "ubuntu" ]] || [[ "$OS_TYPE" == "debian" ]]; then
            if command -v ufw >/dev/null; then
                ufw allow ssh
                ufw --force enable
            else
                apt-get install -y ufw && ufw allow ssh && ufw --force enable
            fi
            echo "已启用 UFW"
        elif [[ "$OS_TYPE" == "centos" ]] || [[ "$OS_TYPE" == "alinux" ]]; then
            systemctl enable --now firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --reload
            echo "已启用 Firewalld"
        fi
        ;;
    "SSH_ROOT")
        sed -i 's/^PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
        grep -q "^PermitRootLogin" /etc/ssh/sshd_config || echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config
        systemctl restart sshd
        echo "已设置 PermitRootLogin prohibit-password"
        ;;
    "SSH_PASS")
        sed -i 's/^PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
        grep -q "^PasswordAuthentication" /etc/ssh/sshd_config || echo "PasswordAuthentication no" >> /etc/ssh/sshd_config
        systemctl restart sshd
        echo "已关闭 SSH 密码认证 (请确保已配置密钥!)"
        ;;
    "SSH_TRIES")
        sed -i 's/^MaxAuthTries.*/MaxAuthTries 4/' /etc/ssh/sshd_config
        grep -q "^MaxAuthTries" /etc/ssh/sshd_config || echo "MaxAuthTries 4" >> /etc/ssh/sshd_config
        systemctl restart sshd
        echo "已设置 MaxAuthTries 4"
        ;;
    "IP_FWD")
        sysctl -w net.ipv4.ip_forward=0
        sed -i 's/^net.ipv4.ip_forward.*/net.ipv4.ip_forward = 0/' /etc/sysctl.conf
        echo "已关闭 IP 转发"
        ;;
    "ICMP_RED")
        sysctl -w net.ipv4.conf.all.accept_redirects=0
        sed -i 's/^net.ipv4.conf.all.accept_redirects.*/net.ipv4.conf.all.accept_redirects = 0/' /etc/sysctl.conf
        echo "已禁止 ICMP 重定向"
        ;;
    "RSYSLOG")
        systemctl enable --now rsyslog
        echo "已启动 Rsyslog"
        ;;
    "AUDITD")
        if [[ "$OS_TYPE" == "ubuntu" ]] || [[ "$OS_TYPE" == "debian" ]]; then
            apt-get install -y auditd && systemctl enable --now auditd
        elif [[ "$OS_TYPE" == "centos" ]] || [[ "$OS_TYPE" == "alinux" ]]; then
            yum install -y audit && systemctl enable --now auditd
        fi
        echo "已尝试安装/启动 Auditd"
        ;;
    "PERM_SHADOW")
        chmod 640 /etc/shadow
        echo "已执行 chmod 640 /etc/shadow"
        ;;
    "PERM_PASSWD")
        chmod 644 /etc/passwd
        echo "已执行 chmod 644 /etc/passwd"
        ;;
    *)
        echo -e "${RED}[!] 未配置该项的自动修复逻辑或需人工干预${NC}"
        ;;
    esac
}

interactive_fix() {
    echo -e "\n=============================================="
    echo -e "           安全风险修复菜单 (Fix Menu)"
    echo -e "=============================================="
    
    if [ ! -s "$TMP_FAIL_IDS" ]; then
        echo -e "${GREEN}✅ 恭喜！未发现高危风险，无需修复。${NC}"
        return
    fi
    
    # 读取失败项到数组
    mapfile -t fail_lines < "$TMP_FAIL_IDS"
    # fail_lines 格式: ID|Description
    
    echo "发现以下风险项:"
    local i=1
    declare -A risk_map
    declare -A desc_map
    
    # 去重显示
    for line in "${fail_lines[@]}"; do
        local id="${line%%|*}"
        local desc="${line#*|}"
        if [[ -z "${desc_map[$id]}" ]]; then
            desc_map[$id]="$desc"
            risk_map[$i]="$id"
            echo -e "  [${YELLOW}$i${NC}] $desc ($id)"
            ((i++))
        fi
    done
    
    echo -e "----------------------------------------------"
    echo -e "请输入要修复的项目编号 (例如: 1 3, all, q退出): "
    read -r selection
    
    if [[ "$selection" == "q" ]] || [[ "$selection" == "quit" ]]; then
        echo "已退出修复。"
        return
    fi
    
    if [[ "$selection" == "all" ]]; then
        echo "正在修复所有检测到的风险..."
        for k in "${!risk_map[@]}"; do
            do_fix "${risk_map[$k]}"
        done
    else
        # 处理输入的数字列表
        for num in $selection; do
            if [[ -n "${risk_map[$num]}" ]]; then
                do_fix "${risk_map[$num]}"
            else
                echo -e "${RED}[!] 无效编号: $num${NC}"
            fi
        done
    fi
    
    echo -e "\n${GREEN}[+] 修复操作已完成。建议重新运行审计进行验证。${NC}"
}

# ---------------------- 报告生成 ----------------------

gen_report_no_clean() {
    echo "# Linux 安全审计报告" > "$REPORT_FILE"
    echo "系统信息: $OS_TYPE $OS_VERSION ($(uname -r))" >> "$REPORT_FILE"
    echo "生成时间: $(date)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "## 🔴 需关注的风险 (Risks)" >> "$REPORT_FILE"
    if [ -s "$TMP_FAIL" ]; then
        echo "| 检查项 | 状态 | 等级 | 建议 |" >> "$REPORT_FILE"
        echo "| --- | --- | --- | --- |" >> "$REPORT_FILE"
        cat "$TMP_FAIL" >> "$REPORT_FILE"
    else
        echo "未发现高/中危风险。" >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"

    echo "## 🟢 已通过 (Passed)" >> "$REPORT_FILE"
    if [ -s "$TMP_PASS" ]; then
        echo "| 检查项 | 状态 | 等级 | 建议 |" >> "$REPORT_FILE"
        echo "| --- | --- | --- | --- |" >> "$REPORT_FILE"
        cat "$TMP_PASS" >> "$REPORT_FILE"
    fi
    
    echo "" >> "$REPORT_FILE"
    echo "## ℹ️ 主机信息 (Host Info)" >> "$REPORT_FILE"
    if [ -s "$TMP_INFO" ]; then
        echo "| 信息项 | 内容 | 备注 |" >> "$REPORT_FILE"
        echo "| --- | --- | --- |" >> "$REPORT_FILE"
        cat "$TMP_INFO" >> "$REPORT_FILE" # Assuming log_result formats correctly for 3 columns or update log_result
    fi
}
# Note: log_result uses 4 columns. For Info, 'Risk' is 'Info'. It fits the table structure above if header matches.
# Let's adjust gen_report_no_clean to match log_result structure (4 cols) or just dump it.
# log_result outputs: | item | status | risk | recommendation |
# So Info table should also have 4 columns.

# 修正 gen_report_no_clean 的 Info 部分
gen_report_no_clean() {
    echo "# Linux 安全审计报告" > "$REPORT_FILE"
    echo "系统信息: $OS_TYPE $OS_VERSION ($(uname -r))" >> "$REPORT_FILE"
    echo "生成时间: $(date)" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    
    echo "## 🔴 需关注的风险 (Risks)" >> "$REPORT_FILE"
    if [ -s "$TMP_FAIL" ]; then
        echo "| 检查项 | 状态 | 等级 | 建议 |" >> "$REPORT_FILE"
        echo "| --- | --- | --- | --- |" >> "$REPORT_FILE"
        cat "$TMP_FAIL" >> "$REPORT_FILE"
    else
        echo "未发现高/中危风险。" >> "$REPORT_FILE"
    fi
    echo "" >> "$REPORT_FILE"

    echo "## 🟢 已通过 (Passed)" >> "$REPORT_FILE"
    if [ -s "$TMP_PASS" ]; then
        echo "| 检查项 | 状态 | 等级 | 建议 |" >> "$REPORT_FILE"
        echo "| --- | --- | --- | --- |" >> "$REPORT_FILE"
        cat "$TMP_PASS" >> "$REPORT_FILE"
    fi
    
    echo "" >> "$REPORT_FILE"
    echo "## ℹ️ 主机信息 (Host Info)" >> "$REPORT_FILE"
    if [ -s "$TMP_INFO" ]; then
        echo "| 项 | 内容 | 级别 | 备注 |" >> "$REPORT_FILE"
        echo "| --- | --- | --- | --- |" >> "$REPORT_FILE"
         cat "$TMP_INFO" >> "$REPORT_FILE"
    fi
}

cleanup() {
    rm -f "$TMP_FAIL" "$TMP_PASS" "$TMP_INFO" "$TMP_FAIL_IDS"
}

# ---------------------- 主逻辑 ----------------------

# CLI 参数解析
if [[ "$1" == "--fix" ]]; then
    MODE="fix"
fi

detect_os
check_root
init_audit

echo -e "${GREEN}[*] 正在执行安全审计...${NC}"
audit_account
audit_network
audit_system
audit_files
audit_host_info

gen_report_no_clean
echo -e "${GREEN}[+] 审计完成。报告已生成于: $REPORT_FILE${NC}"

if [[ "$MODE" == "fix" ]]; then
    interactive_fix
fi

cleanup
