# Antigravity 使用指南 (Guide)

本文件夹包含了从官方网站 `https://antigravity.google/docs/` 下载并翻译的本地化文档。

## 文档目录

### 核心概念

- [首页](./home.md)
- [入门指南](./get-started.md)
- [智能体 (Agent)](./agent.md)
- [模型 (Models)](./models.md)
- [智能体模式与设置](./agent-modes-settings.md)

### 高级功能

- [规则与工作流](./rules-workflows.md)
- [技能 (Skills)](./skills.md)
- [任务组 (Task Groups)](./task-groups.md)
- [浏览器子代理](./browser-subagent.md)
- [安全模式](./secure-mode.md)
- [沙箱化](./sandbox-mode.md)

### 集成与产物

- [MCP 集成](./mcp.md)
- [产物 (Artifacts)](./artifacts.md)
- [任务列表](./task-list.md)
- [实现计划](./implementation-plan.md)
- [演示/走读 (Walkthrough)](./walkthrough.md)
- [浏览器录制](./browser-recordings.md)
- [屏幕截图](./screenshots.md)

### 编辑器 (Editor)

- [知识库 (Knowledge)](./knowledge.md)
- [编辑器概览](./editor.md)
- [标签页与导航 (Tab)](./tab.md)
- [行内命令 (Command)](./command.md)
- [智能体侧边面板](./agent-side-panel.md)
- [编辑器中的变更审查](./review-changes-editor.md)

### 管理器 (Manager)

- [智能体管理器](./agent-manager.md)
- [工作空间 (Workspaces)](./workspaces.md)
- [操场 (Playground)](./playground.md)
- [收件箱 (Inbox)](./inbox.md)
- [对话视图](./conversation-view.md)
- [浏览器子代理视图](./browser-subagent-view.md)
- [窗格 (Panes)](./panes.md)
- [管理器中的变更审查](./review-changes-manager.md)
- [变更侧边栏](./changes-sidebar.md)

### 工具与浏览器

- [终端](./terminal.md)
- [文件操作](./files.md)
- [浏览器功能](./browser.md)
- [Chrome 扩展程序](./chrome-extension.md)
- [白名单与黑名单](./allowlist-denylist.md)
- [独立浏览器配置文件](./separate-chrome-profile.md)

### 其他

- [常见问题 (FAQ)](./faq.md)
- [计划与配额 (Plans)](./plans.md)
- [详细设置](./settings.md)

## 开发辅助工具

### 快速同步脚本 (git_sync.sh)

位于根目录的 `git_sync.sh` 提供了一键同步项目到 GitHub 的功能：

- **快速同步**: 自动 `add + commit + pull + push`。
- **查看状态**: 显示本地改动以及与远程的领先/落后提交数。
- **以本地为准同步**: **[重要]** 当本地确认是最新（如手动删除了文件）且不希望被远程代码覆盖时，使用此选项强制更新远程。
- **发布版本**: 自动打 Tag 并创建 GitHub Release。

**使用方法**:

```bash
./git_sync.sh
```
