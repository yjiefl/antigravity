# Antigravity 编辑器：MCP 集成 (MCP Integration)

Antigravity 支持模型上下文协议 (MCP)，这是一项标准，允许编辑器安全地连接到您的本地工具、数据库和外部服务。这种集成使 AI 能够获得超出编辑器中打开文件的实时上下文。

## 什么是 MCP？

MCP 是 Antigravity 与您更广泛的开发环境之间的桥梁。MCP 允许 Antigravity 在需要时直接获取信息（如数据库模式或日志），而无需手动将这些上下文粘贴到编辑器中。

## 核心特性

### 1. 上下文资源 (Context Resources)

AI 可以从连接的 MCP 服务器读取数据以优化其建议。

**示例**：在编写 SQL 查询时，Antigravity 可以检查您的实时 Neon 或 Supabase 模式，以建议正确的表名和列名。

**示例**：在调试时，编辑器可以从 Netlify 或 Heroku 提取最近的构建日志。

### 2. 自定义工具 (Custom Tools)

MCP 使 Antigravity 能够执行由您连接的服务器定义的特定安全操作。

**示例**：“为此 TODO 创建一个 Linear 问题。”

**示例**：“在 Notion 或 GitHub 中搜索身份验证模式。”

## 如何连接

连接直接通过内置的 MCP Store 进行管理。

1. **访问商店**：打开编辑器侧面板顶部 "..." 下拉菜单中的 MCP Store 面板。
2. **浏览与安装**：从列表中选择任何支持的服务器，然后点击 Install。
3. **身份验证**：按照屏幕提示安全地链接您的账户（如适用）。

安装后，来自服务器的资源和工具将自动在编辑器中可用。

## 连接自定义 MCP 服务器

要连接到自定义 MCP 服务器：

1. 打开编辑器智能体面板顶部的 "..." 下拉菜单。
2. 点击 "Manage MCP Servers"。
3. 点击 "View raw config"。
4. 使用您的自定义 MCP 服务器配置修改 `mcp_config.json`。

## 支持的服务器

MCP Store 目前包含以下集成：

* Airweave, Arize, AlloyDB, Atlassian, BigQuery, Cloud SQL (PostgreSQL/MySQL/SQL Server), Dart, Dataplex, Figma Dev Mode, Firebase, GitHub, Harness, Heroku, Linear, Locofy, Looker, MCP Toolbox, MongoDB, Neon, Netlify, Notion, PayPal, Perplexity Ask, Pinecone, Prisma, Redis, Sequential Thinking, SonarQube, Spanner, Stripe, Supabase 等。
