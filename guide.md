# 项目使用说明 (Guide)

## UI UX Pro Max 技能

本项目已集成 **UI UX Pro Max** 设计智能技能包，旨在提升 AI 在 UI/UX 设计和前端工程方面的表现。

### 功能特色

- **67 种 UI 风格**: 包含 Glassmorphism, Minimalism, Bento Grid 等。
- **96 种配色方案**: 针对不同行业（SaaS, 医疗, 金融等）优化的调色板。
- **57 种字体搭配**: 预设的 Google Fonts 组合。
- **99 条 UX 准则**: 涵盖无障碍性、性能、交互等方面的最佳实践。
- **设计系统生成**: 能够根据需求自动生成完整的设计系统方案。

### 如何使用

当你需要进行 UI/UX 相关任务（如：设计网页、构建组件、优化布局）时，AI 会自动调用此技能。

你也可以手动指定 AI 使用以下命令进行搜索或生成：

```bash
# 生成完整的设计系统方案
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "你的需求描述" --design-system

# 搜索特定领域的风格或最佳实践
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "glassmorphism" --domain style
python3 .agent/skills/ui-ux-pro-max/scripts/search.py "accessibility" --domain ux
```

### 推荐工作流

1. **分析需求**: 确定产品类型、风格关键词和行业。
2. **生成设计系统**: 使用 `--design-system` 获取基础样板。
3. **补充搜索**: 针对图表、字体或特定 UX 问题进行深入搜索。
4. **实施开发**: 根据推荐的配色、字体和样式进行代码编写。
