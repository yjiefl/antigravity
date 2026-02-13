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

# (省略中间审计函数...)

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
    
    # 去重显示（虽然 ID 可能有重复如果审计多次，但这里假设一次审计）
    # 使用关联数组去重
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

# 执行审计 (先生成问题表)
audit_account
audit_network
audit_system
audit_files

# 报告生成 (注意: 报告生成如果很快完成，我们可以在修复前给用户看报告，或者先修复再生成)
# 根据用户需求：先审计 -> 形成问题表 -> 用户选择修复 -> (隐含:修复完结束)
# 我们先生成审计报告，然后如果有 --fix 参数，则进入修复菜单。
# 此时不应删除中间文件，gen_report 需要调整

# 修正 gen_report，使其在 fix 模式下不删除文件，或我们手动控制清理
# 为了简单，我们在 main 最后统一清理

main() {
    echo -e "${GREEN}[*] 正在执行系统审计...${NC}"
    audit_account
    audit_network
    audit_system
    audit_files
    
    # 先生成一份报告（作为审计结果）
    # 但 gen_report 会删除临时文件，所以我们要修改 gen_report 或者先备份
    # 更好的做法：gen_report 不删除文件。
    # 我们用一个专门的 clean_up 函数。
    
    # 暂时重定义 gen_report 的清理逻辑：仅在此处调用时不清理
    # 由于 bash 函数重定义麻烦，我们在 gen_report 结尾注释掉 rm，在 main 显式 rm
}

# 重新定义 gen_report 不包含 rm
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
}

cleanup() {
    rm -f "$TMP_FAIL" "$TMP_PASS" "$TMP_INFO" "$TMP_FAIL_IDS"
}

# 执行流
detect_os
check_root
init_audit

echo -e "${GREEN}[*] 正在执行安全审计...${NC}"
audit_account
audit_network
audit_system
audit_files

gen_report_no_clean
echo -e "${GREEN}[+] 审计完成。报告已生成于: $REPORT_FILE${NC}"

if [[ "$MODE" == "fix" ]]; then
    interactive_fix
fi

cleanup
