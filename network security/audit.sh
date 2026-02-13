#!/bin/bash

# ==============================================================================
# 脚本名称: audit.sh
# 描述: Ubuntu 24.04 (阿里云 ECS) 安全审计脚本
# 作者: AntiGravity (基于 user requirements)
# 版本: 1.0.0
# 日期: 2026-02-13
# 依赖: bash, grep, ss, systemctl, ufw, awk
# 输出: security_audit_report.md
# ==============================================================================

# 设置输出文件路径
REPORT_FILE="./security_audit_report.md"

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
  echo "请使用 root 权限运行此脚本 (Please run as root)"
  exit 1
fi

# 初始化报告函数
init_report() {
  echo "# Ubuntu 24.04 安全审计报告 (Security Audit Report)" > "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  echo "生成时间 (Generated at): $(date '+%Y-%m-%d %H:%M:%S')" >> "$REPORT_FILE"
  echo "主机名 (Hostname): $(hostname)" >> "$REPORT_FILE"
  echo "" >> "$REPORT_FILE"
  
  # 表头
  echo "| 检查项 (Check Item) | 当前状态 (Current Status) | 风险等级 (Risk Level) | 加固建议 (Recommendation) |" >> "$REPORT_FILE"
  echo "| :--- | :--- | :--- | :--- |" >> "$REPORT_FILE"
}

# 记录结果函数
# 参数: $1=检查项, $2=状态, $3=风险等级(High/Medium/Low), $4=建议
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
  
  echo "| $item | $status | $risk | $recommendation |" >> "$REPORT_FILE"
}

# ==============================================================================
# 1. 账号安全审计 (Account Security Audit)
# ==============================================================================
audit_account() {
  echo "开始账号安全审计..."

  # 1.1 检查 Root 账户是否被锁定 (Check if Root account is locked)
  # 理想状态: root 应该被锁定 (L L or NP) 或者禁止直接登录
  local root_status=$(passwd -S root | awk '{print $2}')
  if [[ "$root_status" == "L" ]] || [[ "$root_status" == "NP" ]]; then
    log_result "Root 账户锁定 (Root Account Lock)" "已锁定 (Locked: $root_status)" "Low" "保持现状 (Keep as is)"
  else
    log_result "Root 账户锁定 (Root Account Lock)" "未锁定 (Unlocked: $root_status)" "High" "建议锁定 Root 账户，使用 sudo (Lock root account, use sudo)"
  fi

  # 1.2 检查空口令用户 (Check for empty password accounts)
  local empty_pw_users=$(awk -F: '($2 == "") {print $1}' /etc/shadow)
  if [[ -z "$empty_pw_users" ]]; then
    log_result "空口令用户 (Empty Password Users)" "无 (None)" "Low" "保持现状 (Keep as is)"
  else
    log_result "空口令用户 (Empty Password Users)" "发现: $empty_pw_users" "High" "立即设置密码或锁定账户 (Set password or lock account immediately)"
  fi

  # 1.3 检查 UID 为 0 的非 root 用户 (Check for non-root UID 0 users)
  local uid0_users=$(awk -F: '($3 == 0) {print $1}' /etc/passwd)
  if [[ "$uid0_users" == "root" ]]; then
    log_result "UID 0 非 root 用户 (Non-root UID 0 Users)" "无 (None)" "Low" "保持现状 (Keep as is)"
  else
    log_result "UID 0 非 root 用户 (Non-root UID 0 Users)" "发现: $uid0_users" "High" "除非不仅有 root，否则请立即核查 (Verify immediately if unintended)"
  fi
  
  # 1.4 检查 sudoers 配置 (Check sudoers for NOPASSWD)
  # 简单检查 /etc/sudoers 是否包含 NOPASSWD
  if grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ > /dev/null 2>&1; then
     local nopasswd_entries=$(grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/ | head -n 1) # 只取第一条作为示例
     log_result "Sudo NOPASSWD 配置 (Sudo NOPASSWD)" "存在 (Exists: $nopasswd_entries)" "Medium" "建议移除 NOPASSWD，确保 sudo 需要密码 (Require password for sudo)"
  else
     log_result "Sudo NOPASSWD 配置 (Sudo NOPASSWD)" "未发现 (Not Found)" "Low" "保持现状 (Keep as is)"
  fi
}

# ==============================================================================
# 2. 网络安全审计 (Network Security Audit)
# ==============================================================================
audit_network() {
  echo "开始网络安全审计..."

  # 2.1 检查防火墙状态 (Check Firewall Status)
  if command -v ufw >/dev/null 2>&1; then
      local ufw_status=$(ufw status | grep "Status" | awk '{print $2}')
      if [[ "$ufw_status" == "active" ]]; then
        log_result "UFW 防火墙 (UFW Firewall)" "激活 (Active)" "Low" "保持现状 (Keep as is)"
      else
        log_result "UFW 防火墙 (UFW Firewall)" "未激活 (Inactive)" "High" "建议启用 UFW (Enable UFW)"
      fi
  else
      log_result "UFW 防火墙 (UFW Firewall)" "未安装 (Not Installed)" "Medium" "建议安装并启用 UFW (Install and Enable UFW)"
  fi

  # 2.2 检查 SSH Root 登录 (Check SSH Root Login)
  local sshd_config="/etc/ssh/sshd_config"
  if [ -f "$sshd_config" ]; then
      local permit_root=$(grep "^PermitRootLogin" $sshd_config | awk '{print $2}')
      if [[ "$permit_root" == "no" ]]; then
          log_result "SSH Root 登录 (SSH Root Login)" "禁止 (Disabled)" "Low" "保持现状 (Keep as is)"
      elif [[ "$permit_root" == "prohibit-password" ]]; then
          log_result "SSH Root 登录 (SSH Root Login)" "仅密钥 (Key Only)" "Low" "符合云环境最佳实践 (Good practice)"
      else
          log_result "SSH Root 登录 (SSH Root Login)" "允许 (Enabled: ${permit_root:-default})" "Medium" "建议设置为 no 或 prohibit-password (Recommended: no or prohibit-password)"
      fi
  else
      # 尝试检查 /etc/ssh/sshd_config.d/
      log_result "SSH 配置文件 (SSH Config)" "未找到主配置文件 (Main config not found)" "Medium" "请检查 /etc/ssh/sshd_config.d/"
  fi

  # 2.3 检查 SSH 密码认证 (Check SSH Password Authentication)
  # 阿里云通常使用密钥对，建议关闭密码认证
  local pass_auth=$(grep "^PasswordAuthentication" $sshd_config 2>/dev/null | awk '{print $2}')
  if [[ "$pass_auth" == "no" ]]; then
      log_result "SSH 密码认证 (SSH Password Auth)" "禁止 (Disabled)" "Low" "保持现状 (Keep as is)"
  else
      log_result "SSH 密码认证 (SSH Password Auth)" "允许或未配置 (Enabled/Unset: ${pass_auth:-yes})" "Medium" "建议使用密钥对并关闭密码认证 (Use keys and disable password auth)"
  fi
  
  # 2.4 检查监听端口 (Check Listening Ports)
  # 这里的风险取决于具体业务，这里只列出监听的端口数量供人工审查
  local listen_ports=$(ss -tuln | grep LISTEN | awk '{print $5}' | cut -d: -f2 | sort -u | tr '\n' ' ')
  log_result "监听端口 (Listening Ports)" "端口: $listen_ports" "Info" "请人工确认为必需业务端口 (Review manually)"
}

# ==============================================================================
# 3. 文件系统权限审计 (Filesystem Permissions Audit)
# ==============================================================================
audit_filesystem() {
  echo "开始文件系统权限审计..."

  # 3.1 关键文件权限 (Critical File Permissions)
  # /etc/passwd 644 root:root
  # /etc/shadow 640 root:shadow (or 000)
  # /etc/group 644 root:root
  
  check_file_perm() {
      local file="$1"
      local expected_perm="$2"
      local actual_perm=$(stat -c "%a" "$file" 2>/dev/null)
      if [[ "$actual_perm" == "$expected_perm" ]]; then
          log_result "文件权限 $file" "权限: $actual_perm" "Low" "保持现状 (Keep as is)"
      else
          log_result "文件权限 $file" "权限: ${actual_perm:-Missing}" "Medium" "建议设置为 $expected_perm (Recommended: $expected_perm)"
      fi
  }
  
  check_file_perm "/etc/passwd" "644"
  check_file_perm "/etc/group" "644"
  # shadow 权限在不同发行版略有不同，Ubuntu 通常是 640 root:shadow
  local shadow_perm=$(stat -c "%a" /etc/shadow 2>/dev/null)
  if [[ "$shadow_perm" -le 640 ]]; then
      log_result "文件权限 /etc/shadow" "权限: $shadow_perm" "Low" "保持现状 (Keep as is)"
  else
      log_result "文件权限 /etc/shadow" "权限: $shadow_perm" "High" "建议设置为 640 或更严格 (Recommended: <= 640)"
  fi

  # 3.2 检查全局可写文件的粘滞位 (Sticky bit on world-writable directories)
  # 查找所有全局可写目录，如果没有设置粘滞位，则视为风险
  # 正常情况下 /tmp, /var/tmp 都有粘滞位
  local ww_dirs_no_sticky=$(find / -xdev -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null)
  if [[ -z "$ww_dirs_no_sticky" ]]; then
      log_result "全局可写目录粘滞位 (Sticky Bit on World-Writable Dirs)" "正常 (Normal)" "Low" "保持现状 (Keep as is)"
  else
      # 只显示前3个
      local example_dirs=$(echo "$ww_dirs_no_sticky" | head -n 3 | tr '\n' ' ')
      log_result "全局可写目录粘滞位 (Sticky Bit on World-Writable Dirs)" "发现异常: $example_dirs ..." "Medium" "建议为全局可写目录设置粘滞位 (Set sticky bit: chmod +t)"
  fi
}

# ==============================================================================
# 4. 系统配置与日志审计 (System Config & Log Audit)
# ==============================================================================
audit_system_logs() {
  echo "开始系统配置与日志审计..."

  # 4.1 IP 转发 (IP Forwarding)
  # 如果不是路由器，通常不需要开启
  local ip_forward=$(sysctl net.ipv4.ip_forward 2>/dev/null | awk '{print $3}')
  if [[ "$ip_forward" == "0" ]]; then
      log_result "IP 转发 (IP Forwarding)" "关闭 (Disabled)" "Low" "保持现状 (Keep as is)"
  else
      log_result "IP 转发 (IP Forwarding)" "开启 (Enabled)" "Medium" "如果非路由设备，建议关闭 (Disable if not a router)"
  fi
  
  # 4.2 禁止 ICMP 重定向 (ICMP Redirects)
  local accept_redirects=$(sysctl net.ipv4.conf.all.accept_redirects 2>/dev/null | awk '{print $3}')
  if [[ "$accept_redirects" == "0" ]]; then
      log_result "ICMP 重定向 (ICMP Redirects)" "禁止 (Disabled)" "Low" "保持现状 (Keep as is)"
  else
      log_result "ICMP 重定向 (ICMP Redirects)" "允许 (Enabled)" "Medium" "建议禁止 (Disable: net.ipv4.conf.all.accept_redirects=0)"
  fi

  # 4.3 检查 rsyslog 服务 (Check rsyslog Service)
  if systemctl is-active --quiet rsyslog; then
      log_result "日志服务 (Rsyslog Service)" "运行中 (Active)" "Low" "保持现状 (Keep as is)"
  else
      log_result "日志服务 (Rsyslog Service)" "未运行 (Inactive)" "Medium" "建议启用系统日志服务 (Enable system logging)"
  fi

  # 4.4 检查 auditd 服务 (Check auditd Service)
  # CIS 标准通常要求开启 auditd
  if systemctl is-active --quiet auditd; then
      log_result "审计服务 (Auditd Service)" "运行中 (Active)" "Low" "保持现状 (Keep as is)"
  else
      log_result "审计服务 (Auditd Service)" "未运行/未安装 (Inactive/Missing)" "Medium" "建议安装并启用 auditd (Install and Enable auditd)"
  fi
  
  # 4.5 检查 Logrotate (Check Logrotate)
  # 检查配置文件是否存在
  if [ -f "/etc/logrotate.conf" ]; then
      log_result "日志轮转 (Logrotate)" "配置存在 (Config Found)" "Low" "保持现状 (Keep as is)"
  else
      log_result "日志轮转 (Logrotate)" "配置缺失 (Missing Config)" "High" "建议配置日志轮转 (Configure logrotate)"
  fi
}

# ==============================================================================
# 5. 全面主机信息检查 (Comprehensive Host Information Check)
# ==============================================================================
audit_host_info() {
  echo "开始全面主机信息检查..."

  # 5.1 系统版本与内核 (System Version & Kernel)
  local os_version=$(grep "PRETTY_NAME" /etc/os-release | cut -d'"' -f2)
  local kernel_version=$(uname -r)
  log_result "系统版本 (OS Version)" "$os_version" "Info" "验证是否为最新 LTS (Verify if latest LTS)"
  log_result "内核版本 (Kernel Version)" "$kernel_version" "Info" "定期更新内核以修复漏洞 (Update kernel regularly)"

  # 5.2 CPU 信息 (CPU Information)
  local cpu_model=$(grep "model name" /proc/cpuinfo | head -n 1 | cut -d: -f2 | xargs)
  local cpu_cores=$(grep -c "processor" /proc/cpuinfo)
  log_result "CPU 规格 (CPU spec)" "$cpu_model ($cpu_cores 核/cores)" "Info" "-"

  # 5.3 内存信息 (Memory Information)
  local mem_total=$(free -h | grep "Mem" | awk '{print $2}')
  local mem_free=$(free -h | grep "Mem" | awk '{print $7}')
  log_result "内存总量/可用 (Memory Total/Available)" "$mem_total / $mem_free" "Info" "-"

  # 5.4 磁盘使用情况 (Disk Usage)
  local root_disk_usage=$(df -h / | tail -n 1 | awk '{print $5}')
  log_result "根分区使用率 (Root Partition Usage)" "$root_disk_usage" "Info" "超过 80% 请关注 (Monitor if > 80%)"

  # 5.5 网络配置 (Network Config)
  local ip_addrs=$(ip -4 addr show scope global | grep inet | awk '{print $2}' | tr '\n' ' ')
  local dns_servers=$(grep "^nameserver" /etc/resolv.conf | awk '{print $2}' | tr '\n' ' ')
  log_result "IP 地址 (IP Addresses)" "$ip_addrs" "Info" "-"
  log_result "DNS 服务器 (DNS Servers)" "$dns_servers" "Info" "-"

  # 5.6 系统启动时间 (Uptime)
  local uptime_info=$(uptime -p)
  log_result "系统运行时间 (Uptime)" "$uptime_info" "Info" "-"

  # 5.7 软件包统计 (Package Statistics)
  if command -v dpkg >/dev/null 2>&1; then
      local pkg_count=$(dpkg -l | grep -c "^ii")
      local updates=$(apt-get -s upgrade 2>/dev/null | grep -P '^\d+ upgraded' || echo "Unknown")
      log_result "已安装包数量 (Installed Packages)" "$pkg_count" "Info" "-"
      log_result "待更新包数量 (Pending Updates)" "$updates" "Medium" "建议及时运行 apt upgrade (Run apt upgrade)"
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
  
  echo "" >> "$REPORT_FILE"
  echo "审计完成。报告已生成于 $REPORT_FILE"
  echo "Audit completed. Report generated at $REPORT_FILE"
}

# 执行主函数
main
