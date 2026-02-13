# Network Security Project

## 概述

这是一个针对网络安全与主机加固的项目。目前的重點是针对阿里云 Ubuntu 24.04 的自动化安全审计。

## 目录结构

- `audit.sh`: 安全审计脚本
- `planning.md`: 原始需求规划
- `output/`: 审计报告存放位置
- `spec.md`: 技术规格说明
- `update.md`: 更新日志
- `remote_audit.sh`: 远程审计脚本
- 操作系统: Ubuntu 24.04 (目标阿里云 ECS)
- 权限: 需要 root 权限运行 (脚本内通过 sudo 执行)
- SSH 配置: 需在本地 `~/.ssh/config` 配置免密登陆别名 `aliecs`

## 使用说明

1. **本地直接运行** (仅限 Linux 系统):

   ```bash
   sudo ./audit.sh
   ```

2. **远程审计 (推荐)**:
   在本地 Mac 终端执行：

   ```bash
   chmod +x remote_audit.sh
   ./remote_audit.sh
   ```

   脚本会自动将 `audit.sh` 上传至 `aliecs` 并在运行后拉回报告。
