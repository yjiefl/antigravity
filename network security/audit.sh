#!/bin/bash

# ==============================================================================
# 脚本名称: audit.sh
# 描述: Linux 安全审计脚本 (支持 Ubuntu/CentOS/Debian/Alinux)
# 功能: 安全检查、报告生成、交互式修复
# 作者: AntiGravity
# 版本: 1.2.0
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
        echo "$id" >> "$TMP_FAIL_IDS"
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
    
    # Rsyslog
    if systemctl is-active --quiet rsyslog; then
        log_result "RSYSLOG" "Rsyslog 服务" "运行中" "Low" "-"
    else
        log_result "RSYSLOG" "Rsyslog 服务" "未运行" "Medium" "启用 rsyslog"
    fi
}

# [FS-02] 文件权限
audit_files() {
    echo "正在审计文件权限..."
    local shadow_perm=$(stat -c "%a" /etc/shadow 2>/dev/null)
    if [[ "$shadow_perm" -le 640 ]]; then # 000, 400, 600, 640 are ok for root:shadow (ubuntu) or root:root
         log_result "PERM_SHADOW" "/etc/shadow 权限" "$shadow_perm" "Low" "-"
    else
         log_result "PERM_SHADOW" "/etc/shadow 权限" "$shadow_perm" "High" "设置为 640/600/400"
    fi
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
        # 这是一个复杂的配置，脚本自动修改风险较大，建议仅做简单插入或跳过
        echo -e "${RED}[!] PAM 配置较为复杂，建议手动参考报告修改。跳过自动修复。${NC}"
        ;;
    "FIREWALL")
        if [[ "$OS_TYPE" == "ubuntu" ]] || [[ "$OS_TYPE" == "debian" ]]; then
            if command -v ufw >/dev/null; then
                ufw allow ssh
                ufw --force enable
                echo "已启用 UFW (默认允许 SSH)"
            else
                apt-get install -y ufw && ufw allow ssh && ufw --force enable
            fi
        elif [[ "$OS_TYPE" == "centos" ]] || [[ "$OS_TYPE" == "alinux" ]]; then
            systemctl enable --now firewalld
            firewall-cmd --permanent --add-service=ssh
            firewall-cmd --reload
            echo "已启用 Firewalld"
        fi
        ;;
    "SSH_ROOT")
        sed -i 's/^PermitRootLogin.*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
        # 如果不存在该行，则追加
        grep -q "^PermitRootLogin" /etc/ssh/sshd_config || echo "PermitRootLogin prohibit-password" >> /etc/ssh/sshd_config
        systemctl restart sshd
        echo "已设置 PermitRootLogin prohibit-password 并重启 SSHD"
        ;;
    "SSH_TRIES")
        sed -i 's/^MaxAuthTries.*/MaxAuthTries 4/' /etc/ssh/sshd_config
        grep -q "^MaxAuthTries" /etc/ssh/sshd_config || echo "MaxAuthTries 4" >> /etc/ssh/sshd_config
        systemctl restart sshd
        echo "已设置 MaxAuthTries 4 并重启 SSHD"
        ;;
    "IP_FWD")
        sysctl -w net.ipv4.ip_forward=0
        # 尝试写入 sysctl.conf 持久化
        sed -i 's/^net.ipv4.ip_forward.*/net.ipv4.ip_forward = 0/' /etc/sysctl.conf
        echo "已关闭 IP 转发"
        ;;
    "RSYSLOG")
        systemctl enable --now rsyslog
        echo "已启动 Rsyslog"
        ;;
    "PERM_SHADOW")
        chmod 640 /etc/shadow
        echo "已执行 chmod 640 /etc/shadow"
        ;;
    *)
        echo -e "${RED}[!] 未配置该项的自动修复逻辑${NC}"
        ;;
    esac
}

interactive_fix() {
    echo -e "\n========================================"
    echo -e "         进入交互式修复模式"
    echo -e "========================================"
    
    if [ ! -s "$TMP_FAIL_IDS" ]; then
        echo "✅ 没有发现可修复的风险项。"
        return
    fi
    
    # 读取所有失败ID并去重
    local failed_items=$(sort -u "$TMP_FAIL_IDS")
    
    for id in $failed_items; do
        echo -e "\n${YELLOW}[?] 发现风险项: $id${NC}"
        read -p "    是否尝试修复此项? (y/n) [n]: " choice
        if [[ "$choice" == "y" ]] || [[ "$choice" == "Y" ]]; then
            do_fix "$id"
        else
            echo "    已跳过。"
        fi
    done
    
    echo -e "\n[+] 交互式修复结束。建议重新运行审计以验证结果。"
}

# ---------------------- 报告生成 ----------------------

gen_report() {
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
    
    # 清理
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

# 执行审计
audit_account
audit_network
audit_system
audit_files

# 生成报告
gen_report
echo -e "${GREEN}[+] 审计完成，报告已生成: $REPORT_FILE${NC}"

# 如果是修复模式，进入交互流程
if [[ "$MODE" == "fix" ]]; then
    # 由于 gen_report 删除了临时文件，我们需要在 init 时或 audit 时保存好 ID，
    # 但 gen_report 里的逻辑把文件删了。
    # 修正：gen_report 不应该删除 TMP_FAIL_IDS 如果需要修复。
    # 实际上由于脚本顺序执行，上面的 interactive_fix 应该在 clean 之前调用，或者重新保存。
    # 这里我们简单一点：gen_report 最后再删，或者我们在此之前此调用。
    
    # 重新看上面的 gen_report，它已经执行了 rm。这会导致 fix 没数据。
    # 所以必须调整顺序。
    :
fi

# 调整后的主逻辑流
main() {
    # 1. 审计
    audit_account
    audit_network
    audit_system
    audit_files
    
    # 2. 修复 (如果在 gen_report 之前调用，文件还存在)
    if [[ "$MODE" == "fix" ]]; then
        interactive_fix
        # 修复后可能会改变状态，理论上应该重跑审计生成最终报告，
        # 但简单起见，我们先修复，报告里反映的是修复前的状态（作为证据），
        # 或者用户再次运行查看修复后。
        # 这里维持“先审计生成报告，再修复”的逻辑，
        # 但是 interactive_fix 需要读取 TMP_FAIL_IDS，所以必须在 rm 之前。
    fi
    
    # 3. 报告
    gen_report
    
    echo -e "${GREEN}[+] 流程结束。${NC}"
}

main
