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
- `/docs/antigravity/`: Main documentation folder
- `/docs/antigravity/assets/`: Images and other media
- `/log/debug.log`: Process and debug tracking

## Design Principles
- S.O.L.I.D principles for crawler/utility scripts.
- Consistent terminology mapping for translations.
