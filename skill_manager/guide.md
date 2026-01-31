# Skill 使用指南 (Guide)

欢迎使用 Skill 管理器。本项目集成了一系列强大的 Skill，旨在扩展 AI 的能力，涵盖从专业电力行业分析到日常办公、前端开发、系统管理等多个领域。

本指南将帮助你快速了解并选择适合当前任务的 Skill。

---

## 🏗️ 核心 Skill 类别

### 1. 电力与新能源专家 (Power & Energy)
针对电力行业的专业化工具，具备深度的行业背景知识。

*   **New Energy Power Expert (新能源安全生产调度会材料审核专家)**
    *   **用途**: 深度审核《安全生产总调度会》材料。识别风/光/储运行数据中的逻辑矛盾、计算错误及管理漏洞。
    *   **关键词**: 电力报表审核、运行数据分析、安全生产、逻辑复核。

---

### 2. 基础办公与文档处理 (Office & Document)
大幅提升处理常见办公场景（Excel, PPT, Word, PDF）的效率。

*   **xlsx (Excel 专家)**: 综合电子表格创建、编辑与分析，支持公式、格式化、复杂数据计算及可视化。
*   **pptx (PPT 演示)**: 演示文稿创建与编辑，支持幻灯片设计、内容布局优化及专业格式化。
*   **docx (Word 文档)**: 专业文档创建与编辑，支持格式设置、样式管理、审阅意见及内容提取。
*   **pdf (PDF 工具包)**: 提取文本/表格、合并/拆分文档、填写 PDF 表单及大规模 PDF 数据处理。
*   **doc-coauthoring (协作写作)**: 引导完成文档协作编写的结构化工作流，适用于技术方案、决策文档等。

---

### 3. 前端设计与视觉创意 (Frontend & Design)
用于创建美观、专业且具有高度设计感的界面和艺术作品。

*   **frontend-design (前端设计)**: 创建生产级的现代化网页界面，避免平庸的 AI 审美。
*   **theme-factory (主题工厂)**: 为文档、网页、报告等作品应用一致的主题、色彩和字体。
*   **canvas-design (画布设计)**: 设计海报、平面艺术或其他静态视觉作品。
*   **algorithmic-art (算法艺术)**: 使用 p5.js 代码生成富有创意的算法艺术作品。
*   **brand-guidelines (品牌指南)**: 快速应用官方品牌风格，确保视觉输出的一致性。

---

### 4. 开发、测试与基础设施 (Dev & Infra)
辅助开发者进行代码编写、质量保障及系统调试。

*   **webapp-testing (Web 应用测试)**: 基于 Playwright 测试和验证 Web 应用的功能和性能，支持截图和日志查看。
*   **skill-developer (Skill 开发者)**: 遵循最佳实践创建和管理 Claude Code Skill。
*   **frontend-dev-guidelines (前端开发规范)**: 提供 React/TypeScript 应用的最佳实践指南（Suspense, 性能优化等）。
*   **backend-dev-guidelines (后端开发规范)**: Node.js/Express 微服务的分层架构及 API 规范指南。
*   **error-tracking (错误追踪)**: 快速集成 Sentry 错误监控，确保系统稳定性。
*   **route-tester (路由测试)**: 测试已认证的 API 端点，支持身份验证逻辑调试。
*   **mcp-builder (MCP 构建器)**: 构建高质量 Model Context Protocol 服务器的指南。
*   **langsmith-fetch (LangSmith 调试)**: 获取执行跟踪以调试复杂的 LLM 链和代理行为。

---

### 5. 系统管理与效率提升 (System & Productivity)
自动化日常琐碎任务，管理资源与文件。

*   **file-organizer (文件整理)**: 智能整理计算机上的文件和文件夹，减少混乱。
*   **invoice-organizer (发票管理)**: 自动识别并归类杂乱的发票和收据，便于财务处理。
*   **lead-research-assistant (客户研究)**: 识别高质量潜在客户，分析业务目标并提供接触策略。
*   **domain-name-brainstormer (域名脑暴)**: 生成创意域名并检查多后缀（.com, .io等）的可用性。
*   **changelog-generator (更新日志生成)**: 从 Git 提交历史自动生成面向用户的更新日志。
*   **image-enhancer (图片增强)**: 提高截图或图片的清晰度和分辨率，适用于文档配图。

---

### 6. AI 协作与工作流管理 (AI Workflow)
优化与 AI 的交互过程，确保任务执行的质量。

*   **brainstorming (头脑风暴)**: 在实施任何功能前，深度探索用户意图、需求和设计方案。
*   **executing-plans (计划执行)**: 在带有审核检查点的独立会话中严格执行既定方案。
*   **dispatching-parallel-agents (并行处理)**: 处理可以独立运行、无顺序依赖的多个任务。
*   **developer-growth-analysis (成长分析)**: 分析聊天历史，识别编码模式并提供个性化提升建议。

---

## 🚀 如何触发 Skill

当你的请求中包含相关的意图或关键词时，AI 会自动识别并激活相应的 Skill。你也可以直接指定使用某个 Skill：

*   **直接询问**: “帮我总结这几份发票并整理到文件夹里。”（触发 `invoice-organizer`）
*   **指定任务**: “按照前端开发规范帮我重构这个 React 组件。”（触发 `frontend-dev-guidelines`）
*   **专业场景**: “请以新能源安全生产专家的身份，审核附件中的会议材料。”（触发 `New Energy Power Expert`）

---

## 🛠️ 管理工具

本项目还包含一个 **Skill 管理器**，你可以通过以下方式管理这些技能：

*   **图形界面**: 运行 `python3 skill_manager_gui.py` 开启 GUI。
*   **配置文件**: 详情查看 `skills/skills_config.json`。
*   **更新 Skill**: 使用管理器提供的更新功能保持技能为最新版本。
