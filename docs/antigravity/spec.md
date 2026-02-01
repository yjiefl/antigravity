# Spec: Antigravity Documentation Localized

## Project Goal

Download, translate, and organize the official Antigravity documentation for local offline reading and project reference.

## Mandatory Diagrams (Must)

1. 构架与选型 (Architecture & Selection)
2. 模组关系图 (Module Relationships)
3. 关键流程 (Key Processes)

## Technical Stack

- Source: `https://antigravity.google/docs/`
- Target: Markdown (Chinese Simplified)
- Tools: Browser Crawler, LLM Translation

## Directory Structure

- `/AI/`: AI 相关技能与工具管理。
- `/apps/`: 独立应用程序（如视频下载器等）。
- `/services/`: 后端服务或特定功能模块。
- `/docs/antigravity/`: Antigravity 官方文档本地化整理。
- `/log/`: 项目运行与调试日志。
- `/现场安全风险管控系统/`: 特定业务系统模块。
- `/docs/公文范本/`: 公文范本数据处理。

## Design Principles

- S.O.L.I.D principles for crawler/utility scripts.
- Consistent terminology mapping for translations.
