# Ubuntu 24.04 安全审计报告 (Security Audit Report)

生成时间 (Generated at): 2026-02-13 14:32:07
主机名 (Hostname): MacBook-Air-M3-2024.local

| 检查项 (Check Item) | 当前状态 (Current Status) | 风险等级 (Risk Level) | 加固建议 (Recommendation) |
| :--- | :--- | :--- | :--- |
| Root 账户锁定 (Root Account Lock) | 未锁定 (Unlocked: ) | High | 建议锁定 Root 账户，使用 sudo (Lock root account, use sudo) |
| 空口令用户 (Empty Password Users) | 无 (None) | Low | 保持现状 (Keep as is) |
| UID 0 非 root 用户 (Non-root UID 0 Users) | 无 (None) | Low | 保持现状 (Keep as is) |
| Sudo NOPASSWD 配置 (Sudo NOPASSWD) | 未发现 (Not Found) | Low | 保持现状 (Keep as is) |
| UFW 防火墙 (UFW Firewall) | 未安装 (Not Installed) | Medium | 建议安装并启用 UFW (Install and Enable UFW) |
| SSH Root 登录 (SSH Root Login) | 允许 (Enabled: default) | Medium | 建议设置为 no 或 prohibit-password (Recommended: no or prohibit-password) |
| SSH 密码认证 (SSH Password Auth) | 允许或未配置 (Enabled/Unset: yes) | Medium | 建议使用密钥对并关闭密码认证 (Use keys and disable password auth) |
| 监听端口 (Listening Ports) | 端口:  | Info | 请人工确认为必需业务端口 (Review manually) |
| 文件权限 /etc/passwd | 权限: Missing | Medium | 建议设置为 644 (Recommended: 644) |
| 文件权限 /etc/group | 权限: Missing | Medium | 建议设置为 644 (Recommended: 644) |
| 文件权限 /etc/shadow | 权限:  | Low | 保持现状 (Keep as is) |
