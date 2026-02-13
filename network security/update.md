# 更新日志 (Update Log)

## 更新情况

### 2026-02-13 14:10

- [x] 初始化项目结构 (README.md, spec.md, update.md) - 2026-02-13 14:10:00
- [x] 编写一个非破坏性的 Bash 脚本 (`audit.sh`)，用于审计 Ubuntu 24.04 (阿里云 ECS) 的安全性，并提供一个本地控制器 (`remote_audit.sh`) 通过 SSH `aliecs` 免密执行远端审计。
- [x] 扩展 audit.sh 增加全面主机信息检查 (系统、硬件、网络、存储等) - 2026-02-13 14:35:00
- [x] 增加 remote_audit.sh 支持远端免密审计 (ssh aliecs) - 2026-02-13 14:40:00
- [x] 修复因本地报告文件权限导致的 scp 下载失败问题 - 2026-02-13 14:50:00
- [x] 优化 security_audit_report.md 结构，按"通过"和"未通过"分类展示，确保所有项被记录 - 2026-02-13 14:58:00
- [x] 修改 remote_audit.sh 支持用户输入 SSH 命令 (交互式输入 ssh 连接字符串) - 2026-02-13 15:05:00
- [x] 优化报告输出路径：保存至 `output/` 目录并添加日期时间戳 - 2026-02-13 21:30:00
- [x] 增加登录失败锁定及 SSH 重试次数检查 - 2026-02-13 21:40:00
- [x] 修复 git_sync.sh 在 macOS zsh 环境下输入 'd' 无法查看差异的问题，并增加菜单循环逻辑 - 2026-02-13 18:30:00

### 待完善

输出到：/Users/yangjie/code/antigravity/network security/output，文件名带日期时间戳
