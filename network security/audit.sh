#!/bin/bash

# ==============================================================================
# 脚本名称: audit.sh
# 描述: Ubuntu 24.04 (阿里云 ECS) 安全审计脚本
# 作者: AntiGravity (基于 user requirements)
# 版本: 1.1.0
# 日期: 2026-02-13
# 依赖: bash, grep, ss, systemctl, ufw, awk
# 输出: security_audit_report.md
# ==============================================================================

# 设置输出文件路径
REPORT_FILE="./security_audit_report.md"

# 临时文件路径
TMP_FAIL="/tmp/audit_fail.tmp"
TMP_PASS="/tmp/audit_pass.tmp"
TMP_INFO="/tmp/audit_info.tmp"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
  echo "请使用 root 权限运行此脚本 (Please run as root)"
  exit 1
fi

# 清理并初始化临时文件
init_temp_files() {
  > "$TMP_FAIL"
  > "$TMP_PASS"
  > "$TMP_INFO"
}

# 初始化报告函数 (仅写入标题和主机信息)
init_report() {
  init_temp_files
  echo "# Ubuntu 24.04 安全审计报告 (Security Audit Report)" > "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "生成时间 (Generated at): $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
  echo "主机名 (Hostname): $(hostname)" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
}

# 记录结果函数
# 参数: $1=检查项, $2=状态/证据, $3=风险等级(High/Medium/Low/Info), $4=建议
log_result() {
  local item="$1"
  local status="$2"
  local risk="$3"
  local recommendation="$4"
  
  # Markdown 表格行，处理换行符以便在表格中显示
  # 替换 | 为 \| 以防破坏表格结构
  item="${item//|/\\|}"
  status="${status//|/\\|}"
  recommendation="${recommendation//|/\\|}"
  
  # 统一格式
  local row="| $item | $status | $risk | $recommendation |"

  # 根据风险等级分类写入不同的临时文件
  # High/Medium -> 风险项 (Fail)
  # Low -> 通过项 (Pass) - 假设 Low 代表符合预期或无风险
  # Info -> 信息项
  if [[ "$risk" == "High" ]] || [[ "$risk" == "Medium" ]]; then
    echo "$row" >> "$TMP_FAIL"
  elif [[ "$risk" == "Low" ]]; then
    # 对于 Low 风险，通常意味着"安全"或"可接受"，我们将其放入已通过
    # 并将表头略微调整以适应
    echo "$row" >> "$TMP_PASS"
  else
    echo "$row" >> "$TMP_INFO"
  fi
}

# 生成最终报告
generate_report() {
  # 1. 发现的风险 (Detected Risks) - 即未通过项
  echo "## 🔴 发现的风险 / Detected Risks" >> "$REPORT_FILE"
  echo "> 以下项目存在安全风险，建议优先处理。" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  
  if [ -s "$TMP_FAIL" ]; then
    echo "| 检查项 (Check Item) | 用证/状态 (Evidence/Status) | 风险等级 (Risk) | 加固建议 (Recommendation) |" >> "$REPORT_FILE"
    echo "| :--- | :--- | :--- | :--- |" >> "$REPORT_FILE"
    cat "$TMP_FAIL" >> "$REPORT_FILE"
  else
    echo "✅ 恭喜！未发现高/中危风险 (No High/Medium risks found)." >> "$REPORT_FILE"
  fi
  echo "" >> "$REPORT_FILE"

  # 2. 已通过的检查 (Passed Checks)
  echo "## 🟢 已通过的检查 / Passed Checks" >> "$REPORT_FILE"
  echo "> 以下项目符合安全基线要求或风险极低。" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"

  if [ -s "$TMP_PASS" ]; then
    echo "| 检查项 (Check Item) | 当前状态 (Current Status) | 评估 (Eval) | 备注 (Note) |" >> "$REPORT_FILE"
    echo "| :--- | :--- | :--- | :--- |" >> "$REPORT_FILE"
    cat "$TMP_PASS" >> "$REPORT_FILE"
  else
    echo "无已通过项 (No passed items found - check script logic)." >> "$REPORT_FILE"
  fi
  echo "" >> "$REPORT_FILE"

  # 3. 主机信息 (Host Information)
  echo "## ℹ️ 主机信息 / Host Information" >> "$REPORT_FILE"
  echo "> 仅供参考的系统基础信息。" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"

  if [ -s "$TMP_INFO" ]; then
    echo "| 信息项 (Info Item) | 内容 (Content) | 级别 (Level) | 备注 (Note) |" >> "$REPORT_FILE"
    echo "| :--- | :--- | :--- | :--- |" >> "$REPORT_FILE"
    cat "$TMP_INFO" >> "$REPORT_FILE"
  fi
  echo "" >> "$REPORT_FILE"

  # 清理临时文件
  rm -f "$TMP_FAIL" "$TMP_PASS" "$TMP_INFO"
}

# ==============================================================================
# 1. 账号安全审计 (Account Security Audit)
# ==============================================================================
audit_account() {
  echo "开始账号安全审计..."

  # 1.1 检查 Root 账户是否被锁定
  local root_status=$(passwd -S root | awk '{print $2}')
  if [[ "$root_status" == "L" ]] || [[ "$root_status" == "NP" ]]; then
    log_result "Root 账户锁定" "已锁定 ($root_status)" "Low" "符合要求"
  else
    log_result "Root 账户锁定" "未锁定 ($root_status)" "High" "建议锁定 Root 账户，使用 sudo"
  fi

  # 1.2 检查空口令用户
  local empty_pw_users=$(awk -F: '($2 == "") {print $1}' /etc/shadow)
  if [[ -z "$empty_pw_users" ]]; then
    log_result "空口令用户" "无" "Low" "符合要求"
  else
    log_result "空口令用户" "发现: $empty_pw_users" "High" "立即设置密码或锁定账户"
  fi

  # 1.3 检查 UID 为 0 的非 root 用户
  local uid0_users=$(awk -F: '($3 == 0) {print $1}' /etc/passwd)
  if [[ "$uid0_users" == "root" ]]; then
    log_result "UID 0 非 root 用户" "无" "Low" "符合要求"
  else
    log_result "UID 0 非 root 用户" "发现: $uid0_users" "High" "请立即核查"
  fi
  
  # 1.4 检查 sudoers 配置
  if grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ > /dev/null 2>&1; then
     local nopasswd_entries=$(grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ | head -n 1) 
     log_result "Sudo NOPASSWD 配置" "存在 ($nopasswd_entries)" "Medium" "建议移除 NOPASSWD"
  else
     log_result "Sudo NOPASSWD 配置" "未发现" "Low" "符合要求"
  fi

  # 1.5 检查登录失败锁定策略 (PAM faillock)
  if grep -E "pam_faillock.so" /etc/pam.d/common-auth > /dev/null 2>&1; then
      local deny_val=$(grep "deny=" /etc/pam.d/common-auth | sed -n 's/.*deny=\([0-9]*\).*/\1/p' | head -n 1)
      log_result "登录失败锁定策略" "已配置 (deny=${deny_val:-默认})" "Low" "符合要求"
  else
      log_result "登录失败锁定策略" "未配置" "Medium" "建议配置 pam_faillock 以防止暴力破解"
  fi
}

# ==============================================================================
# 2. 网络安全审计 (Network Security Audit)
# ==============================================================================
audit_network() {
  echo "开始网络安全审计..."

  # 2.1 检查防火墙状态
  if command -v ufw >/dev/null 2>&1; then
      local ufw_status=$(ufw status | grep "Status" | awk '{print $2}')
      if [[ "$ufw_status" == "active" ]]; then
        log_result "UFW 防火墙" "激活" "Low" "符合要求"
      else
        log_result "UFW 防火墙" "未激活" "High" "建议启用 UFW"
      fi
  else
      log_result "UFW 防火墙" "未安装" "Medium" "建议安装并启用 UFW"
  fi

  # 2.2 检查 SSH Root 登录
  local sshd_config="/etc/ssh/sshd_config"
  if [ -f "$sshd_config" ]; then
      local permit_root=$(grep "^PermitRootLogin" $sshd_config | awk '{print $2}')
      if [[ "$permit_root" == "no" ]]; then
          log_result "SSH Root 登录" "禁止" "Low" "符合要求"
      elif [[ "$permit_root" == "prohibit-password" ]]; then
          log_result "SSH Root 登录" "仅密钥" "Low" "符合云环境最佳实践"
      else
          log_result "SSH Root 登录" "允许 ($permit_root)" "Medium" "建议设置为 no 或 prohibit-password"
      fi
  else
      log_result "SSH 配置文件" "未找到主配置文件" "Medium" "请检查 /etc/ssh/sshd_config.d/"
  fi

  # 2.3 检查 SSH 密码认证
  local pass_auth=$(grep "^PasswordAuthentication" $sshd_config 2>/dev/null | awk '{print $2}')
  if [[ "$pass_auth" == "no" ]]; then
      log_result "SSH 密码认证" "禁止" "Low" "符合要求"
  else
      log_result "SSH 密码认证" "允许或未配置 ($pass_auth)" "Medium" "建议使用密钥对并关闭密码认证"
  fi
  
  # 2.4 检查 SSH 最大认证尝试次数 (MaxAuthTries)
  local max_tries=$(grep "^MaxAuthTries" $sshd_config 2>/dev/null | awk '{print $2}')
  if [[ -n "$max_tries" ]] && [[ "$max_tries" -le 4 ]]; then
      log_result "SSH 最大尝试次数" "$max_tries" "Low" "符合要求 (<=4)"
  else
      log_result "SSH 最大尝试次数" "${max_tries:-默认(6)}" "Medium" "建议设置为 4 或更小"
  fi

  # 2.5 检查监听端口
  local listen_ports=$(ss -tuln | grep LISTEN | awk '{print $5}' | cut -d: -f2 | sort -u | tr '\n' ' ')
  log_result "监听端口" "端口: $listen_ports" "Info" "请人工确认为必需业务端口"
}

# ==============================================================================
# 3. 文件系统权限审计 (Filesystem Permissions Audit)
# ==============================================================================
audit_filesystem() {
  echo "开始文件系统权限审计..."

  # 3.1 关键文件权限
  check_file_perm() {
      local file="$1"
      local expected_perm="$2"
      local actual_perm=$(stat -c "%a" "$file" 2>/dev/null)
      if [[ "$actual_perm" == "$expected_perm" ]]; then
          log_result "文件权限 $file" "$actual_perm" "Low" "符合要 ($expected_perm)"
      else
          log_result "文件权限 $file" "$actual_perm" "Medium" "建议设置为 $expected_perm"
      fi
  }
  
  check_file_perm "/etc/passwd" "644"
  check_file_perm "/etc/group" "644"
  
  local shadow_perm=$(stat -c "%a" /etc/shadow 2>/dev/null)
  if [[ "$shadow_perm" -le 640 ]]; then
      log_result "文件权限 /etc/shadow" "$shadow_perm" "Low" "符合要求 (<=640)"
  else
      log_result "文件权限 /etc/shadow" "$shadow_perm" "High" "建议设置为 640 或更严格"
  fi

  # 3.2 检查全局可写文件的粘滞位
  local ww_dirs_no_sticky=$(find / -xdev -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null)
  if [[ -z "$ww_dirs_no_sticky" ]]; then
      log_result "全局可写目录粘滞位" "正常" "Low" "符合要求"
  else
      # 截取前3个目录作为示例证据
      local example_dirs=$(echo "$ww_dirs_no_sticky" | head -n 3 | tr '\n' ' ')
      log_result "全局可写目录粘滞位" "异常: $example_dirs ..." "Medium" "建议为全局可写目录设置粘滞位 (+t)"
  fi
}

# ==============================================================================
# 4. 系统配置与日志审计 (System Config & Log Audit)
# ==============================================================================
audit_system_logs() {
  echo "开始系统配置与日志审计..."

  # 4.1 IP 转发
  local ip_forward=$(sysctl net.ipv4.ip_forward 2>/dev/null | awk '{print $3}')
  if [[ "$ip_forward" == "0" ]]; then
      log_result "IP 转发" "关闭" "Low" "符合要求"
  else
      log_result "IP 转发" "开启" "Medium" "非路由设备建议关闭"
  fi
  
  # 4.2 ICMP 重定向
  local accept_redirects=$(sysctl net.ipv4.conf.all.accept_redirects 2>/dev/null | awk '{print $3}')
  if [[ "$accept_redirects" == "0" ]]; then
      log_result "ICMP 重定向" "禁止" "Low" "符合要求"
  else
      log_result "ICMP 重定向" "允许" "Medium" "建议禁止"
  fi

  # 4.3 检查 rsyslog 服务
  if systemctl is-active --quiet rsyslog; then
      log_result "日志服务 (Rsyslog)" "运行中" "Low" "符合要求"
  else
      log_result "日志服务 (Rsyslog)" "未运行" "Medium" "建议启用系统日志服务"
  fi

  # 4.4 检查 auditd 服务
  if systemctl is-active --quiet auditd; then
      log_result "审计服务 (Auditd)" "运行中" "Low" "符合要求"
  else
      log_result "审计服务 (Auditd)" "未运行/未安装" "Medium" "建议安装并启用 auditd"
  fi
  
  # 4.5 检查 Logrotate
  if [ -f "/etc/logrotate.conf" ]; then
      log_result "日志轮转 (Logrotate)" "配置存在" "Low" "符合要求"
  else
      log_result "日志轮转 (Logrotate)" "配置缺失" "High" "建议配置日志轮转"
  fi
}

# ==============================================================================
# 5. 全面主机信息检查 (Comprehensive Host Information Check)
# ==============================================================================
audit_host_info() {
  echo "开始全面主机信息检查..."

  # 5.1 系统版本与内核
  local os_version=$(grep "PRETTY_NAME" /etc/os-release | cut -d'"' -f2)
  local kernel_version=$(uname -r)
  log_result "系统版本" "$os_version" "Info" "LTS 检查"
  log_result "内核版本" "$kernel_version" "Info" "漏洞修复检查"

  # 5.2 CPU 信息
  local cpu_model=$(grep "model name" /proc/cpuinfo | head -n 1 | cut -d: -f2 | xargs)
  local cpu_cores=$(grep -c "processor" /proc/cpuinfo)
  log_result "CPU 规格" "$cpu_model ($cpu_cores 核)" "Info" "-"

  # 5.3 内存信息
  local mem_total=$(free -h | grep "Mem" | awk '{print $2}')
  local mem_free=$(free -h | grep "Mem" | awk '{print $7}')
  log_result "内存总量/可用" "$mem_total / $mem_free" "Info" "-"

  # 5.4 磁盘使用情况
  local root_disk_usage=$(df -h / | tail -n 1 | awk '{print $5}')
  log_result "根分区使用率" "$root_disk_usage" "Info" "超过 80% 需关注"

  # 5.5 网络配置
  local ip_addrs=$(ip -4 addr show scope global | grep inet | awk '{print $2}' | tr '\n' ' ')
  local dns_servers=$(grep "^nameserver" /etc/resolv.conf | awk '{print $2}' | tr '\n' ' ')
  log_result "IP 地址" "$ip_addrs" "Info" "-"
  log_result "DNS 服务器" "$dns_servers" "Info" "-"

  # 5.6 系统启动时间
  local uptime_info=$(uptime -p)
  log_result "系统运行时间" "$uptime_info" "Info" "-"

  # 5.7 软件包统计
  if command -v dpkg >/dev/null 2>&1; then
      local pkg_count=$(dpkg -l | grep -c "^ii")
      local updates=$(apt-get -s upgrade 2>/dev/null | grep -P '^\d+ upgraded' || echo "Unknown")
      log_result "已安装包数量" "$pkg_count" "Info" "-"
      log_result "待更新包数量" "$updates" "Medium" "建议及时运行 apt upgrade"
  fi
}

# ==============================================================================
# 主逻辑 (Main Logic)
# ==============================================================================
main() {
  init_report
  audit_account
  audit_network
  audit_filesystem
  audit_system_logs
  audit_host_info
  generate_report
  
  echo "审计完成。报告已生成于 $REPORT_FILE"
  echo "Audit completed. Report generated at $REPORT_FILE"
}

# 执行主函数
main
