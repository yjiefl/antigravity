# 技能 (Skills)

技能是扩展智能体能力的开放标准。一个技能就是一个包含 `SKILL.md` 文件（内含智能体可遵循的指令）的文件夹。

**什么是技能？**
技能是可重用的知识包，包括：
* 针对特定任务的指令。
* 最佳实践和约定。
* 可选的脚本和资源。

**技能存储路径：**
* **工作空间**：`<workspace-root>/.agent/skills/<skill-folder>/`
* **全局**：`~/.gemini/antigravity/global_skills/<skill-folder>/`

**创建一个技能：**
1. 在上述技能目录之一中创建一个文件夹。
2. 添加一个包含 YAML Frontmatter 的 `SKILL.md` 文件：
```markdown
---
name: my-skill
description: 帮助完成特定任务。
---
# 我的技能
详细指令...
```

**智能体如何使用技能：**
智能体根据技能说明自动发现技能。如果技能看起来与您的任务相关，智能体将“激活”该技能并遵循其指令。
