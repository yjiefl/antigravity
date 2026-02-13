# Ubuntu 24.04 安全审计报告 (Security Audit Report)

生成时间 (Generated at): 2026-02-13 14:50:47
主机名 (Hostname): iZwz98d6wedcf34jrwb3xeZ

| 检查项 (Check Item) | 当前状态 (Current Status) | 风险等级 (Risk Level) | 加固建议 (Recommendation) |
| :--- | :--- | :--- | :--- |
| Root 账户锁定 (Root Account Lock) | 未锁定 (Unlocked: P) | High | 建议锁定 Root 账户，使用 sudo (Lock root account, use sudo) |
| 空口令用户 (Empty Password Users) | 无 (None) | Low | 保持现状 (Keep as is) |
| UID 0 非 root 用户 (Non-root UID 0 Users) | 无 (None) | Low | 保持现状 (Keep as is) |
| Sudo NOPASSWD 配置 (Sudo NOPASSWD) | 未发现 (Not Found) | Low | 保持现状 (Keep as is) |
| UFW 防火墙 (UFW Firewall) | 激活 (Active) | Low | 保持现状 (Keep as is) |
| SSH Root 登录 (SSH Root Login) | 允许 (Enabled: yes) | Medium | 建议设置为 no 或 prohibit-password (Recommended: no or prohibit-password) |
| SSH 密码认证 (SSH Password Auth) | 允许或未配置 (Enabled/Unset: yes) | Medium | 建议使用密钥对并关闭密码认证 (Use keys and disable password auth) |
| 监听端口 (Listening Ports) | 端口:  22 32983 53 8888  | Info | 请人工确认为必需业务端口 (Review manually) |
| 文件权限 /etc/passwd | 权限: 644 | Low | 保持现状 (Keep as is) |
| 文件权限 /etc/group | 权限: 644 | Low | 保持现状 (Keep as is) |
| 文件权限 /etc/shadow | 权限: 640 | Low | 保持现状 (Keep as is) |
| 全局可写目录粘滞位 (Sticky Bit on World-Writable Dirs) | 发现异常: /www/wwwlogs/go /www/server/go_project/vhost/scripts /www/server/panel/data/safeCloud/rules/crypto  ... | Medium | 建议为全局可写目录设置粘滞位 (Set sticky bit: chmod +t) |
| IP 转发 (IP Forwarding) | 开启 (Enabled) | Medium | 如果非路由设备，建议关闭 (Disable if not a router) |
| ICMP 重定向 (ICMP Redirects) | 禁止 (Disabled) | Low | 保持现状 (Keep as is) |
| 日志服务 (Rsyslog Service) | 运行中 (Active) | Low | 保持现状 (Keep as is) |
| 审计服务 (Auditd Service) | 未运行/未安装 (Inactive/Missing) | Medium | 建议安装并启用 auditd (Install and Enable auditd) |
| 日志轮转 (Logrotate) | 配置存在 (Config Found) | Low | 保持现状 (Keep as is) |
| 系统版本 (OS Version) | Ubuntu 24.04.3 LTS | Info | 验证是否为最新 LTS (Verify if latest LTS) |
| 内核版本 (Kernel Version) | 6.8.0-90-generic | Info | 定期更新内核以修复漏洞 (Update kernel regularly) |
| CPU 规格 (CPU spec) | Intel(R) Xeon(R) Platinum (2 核/cores) | Info | - |
| 内存总量/可用 (Memory Total/Available) | 1.6Gi / 1.1Gi | Info | - |
| 根分区使用率 (Root Partition Usage) | 15% | Info | 超过 80% 请关注 (Monitor if > 80%) |
| IP 地址 (IP Addresses) | 172.19.226.58/20 172.17.0.1/16  | Info | - |
| DNS 服务器 (DNS Servers) | 127.0.0.53  | Info | - |
| 系统运行时间 (Uptime) | up 2 days, 22 hours, 25 minutes | Info | - |
| 已安装包数量 (Installed Packages) | 907 | Info | - |
| 待更新包数量 (Pending Updates) | 21 upgraded, 0 newly installed, 0 to remove and 2 not upgraded. | Medium | 建议及时运行 apt upgrade (Run apt upgrade) |
