# 更新日志 (Update Log)

## 2026-02-13

- [x] 初始化项目结构 (README.md, spec.md, update.md) - 2026-02-13 14:10:00
- [x] 编写一个非破坏性的 Bash 脚本 (`audit.sh`)，用于审计 Ubuntu 24.04 (阿里云 ECS) 的安全性，并提供一个本地控制器 (`remote_audit.sh`) 通过 SSH `aliecs` 免密执行远端审计。
- [x] 扩展 audit.sh 增加全面主机信息检查 (系统、硬件、网络、存储等) - 2026-02-13 14:35:00
- [x] 增加 remote_audit.sh 支持远端免密审计 (ssh aliecs) - 2026-02-13 14:40:00
