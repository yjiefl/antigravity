# Ubuntu 24.04 安全审计报告 (Security Audit Report)

生成时间 (Generated at): 2026-02-13 21:26:05
主机名 (Hostname): iZwz98d6wedcf34jrwb3xeZ

## 🔴 发现的风险 / Detected Risks
> 以下项目存在安全风险，建议优先处理。

| 检查项 (Check Item) | 用证/状态 (Evidence/Status) | 风险等级 (Risk) | 加固建议 (Recommendation) |
| :--- | :--- | :--- | :--- |
| Root 账户锁定 | 未锁定 (P) | High | 建议锁定 Root 账户，使用 sudo |
| SSH Root 登录 | 允许 (yes) | Medium | 建议设置为 no 或 prohibit-password |
| SSH 密码认证 | 允许或未配置 (yes) | Medium | 建议使用密钥对并关闭密码认证 |
| 全局可写目录粘滞位 | 异常: /www/wwwlogs/go /www/server/go_project/vhost/scripts /www/server/panel/data/safeCloud/rules/crypto  ... | Medium | 建议为全局可写目录设置粘滞位 (+t) |
| IP 转发 | 开启 | Medium | 非路由设备建议关闭 |
| 审计服务 (Auditd) | 未运行/未安装 | Medium | 建议安装并启用 auditd |
| 待更新包数量 | 21 upgraded, 0 newly installed, 0 to remove and 2 not upgraded. | Medium | 建议及时运行 apt upgrade |

## 🟢 已通过的检查 / Passed Checks
> 以下项目符合安全基线要求或风险极低。

| 检查项 (Check Item) | 当前状态 (Current Status) | 评估 (Eval) | 备注 (Note) |
| :--- | :--- | :--- | :--- |
| 空口令用户 | 无 | Low | 符合要求 |
| UID 0 非 root 用户 | 无 | Low | 符合要求 |
| Sudo NOPASSWD 配置 | 未发现 | Low | 符合要求 |
| UFW 防火墙 | 激活 | Low | 符合要求 |
| 文件权限 /etc/passwd | 644 | Low | 符合要 (644) |
| 文件权限 /etc/group | 644 | Low | 符合要 (644) |
| 文件权限 /etc/shadow | 640 | Low | 符合要求 (<=640) |
| ICMP 重定向 | 禁止 | Low | 符合要求 |
| 日志服务 (Rsyslog) | 运行中 | Low | 符合要求 |
| 日志轮转 (Logrotate) | 配置存在 | Low | 符合要求 |

## ℹ️ 主机信息 / Host Information
> 仅供参考的系统基础信息。

| 信息项 (Info Item) | 内容 (Content) | 级别 (Level) | 备注 (Note) |
| :--- | :--- | :--- | :--- |
| 监听端口 | 端口:  22 32983 53 8888  | Info | 请人工确认为必需业务端口 |
| 系统版本 | Ubuntu 24.04.3 LTS | Info | LTS 检查 |
| 内核版本 | 6.8.0-90-generic | Info | 漏洞修复检查 |
| CPU 规格 | Intel(R) Xeon(R) Platinum (2 核) | Info | - |
| 内存总量/可用 | 1.6Gi / 1.0Gi | Info | - |
| 根分区使用率 | 15% | Info | 超过 80% 需关注 |
| IP 地址 | 172.19.226.58/20 172.17.0.1/16  | Info | - |
| DNS 服务器 | 127.0.0.53  | Info | - |
| 系统运行时间 | up 3 days, 5 hours, 0 minutes | Info | - |
| 已安装包数量 | 907 | Info | - |

