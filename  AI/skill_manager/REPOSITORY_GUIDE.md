# Skill仓库浏览功能说明

## 🎉 新功能

Skill管理器现在支持**浏览预设仓库**功能!你可以快速访问精选的skill仓库,包括官方仓库和优质开源资源。

## 📚 预设仓库列表

### 1. Anthropic官方Skills
- **仓库地址**: https://github.com/anthropics/skills
- **描述**: Anthropic官方skill仓库
- **包含skills**: 官方示例和推荐skills

### 2. Awesome AI Skills
- **仓库地址**: https://github.com/awesome-ai/skills
- **描述**: 精选AI技能集合
- **包含skills**: 
  - code-analyzer - 代码分析工具
  - doc-generator - 文档生成器

### 3. Community Skills Hub
- **仓库地址**: https://github.com/community/skills-hub
- **描述**: 社区贡献的skill集合
- **包含skills**:
  - data-processor - 数据处理工具
  - api-helper - API辅助工具

## 🚀 使用方法

### 方法1: 浏览并选择

1. 点击"📚 浏览仓库"按钮
2. 在弹出窗口中浏览不同的仓库(使用选项卡切换)
3. 查看每个仓库的描述和可用skills
4. **双击**你想要的skill,自动填充URL
5. 返回主界面,点击"下载"按钮

### 方法2: 直接下载

1. 点击"📚 浏览仓库"按钮
2. 选择一个skill
3. 点击"下载选中的Skill"按钮
4. 自动开始下载和安装

### 方法3: 复制仓库URL

1. 点击"📚 浏览仓库"按钮
2. 点击仓库URL(蓝色链接)
3. URL自动复制到剪贴板
4. 可以粘贴到其他地方使用

## 💡 功能特点

- ✅ **分类展示** - 使用选项卡分类显示不同仓库
- ✅ **快速选择** - 双击skill即可选择
- ✅ **一键下载** - 选择后可直接下载
- ✅ **URL复制** - 点击仓库URL自动复制
- ✅ **详细信息** - 显示每个skill的名称和描述

## 🔧 自定义仓库

如果你想添加自己的仓库,可以编辑 `skill_manager_gui.py` 文件中的 `PRESET_REPOSITORIES` 列表:

```python
PRESET_REPOSITORIES = [
    {
        'name': '你的仓库名称',
        'url': 'https://github.com/your/repo',
        'description': '仓库描述',
        'skills': [
            {
                'name': 'skill-name',
                'url': 'https://github.com/your/skill.git',
                'description': 'skill描述'
            },
        ]
    },
]
```

## 📝 注意事项

1. **网络连接**: 下载需要网络连接
2. **Git依赖**: 从Git仓库下载需要安装Git
3. **URL格式**: 支持Git仓库URL和ZIP文件URL
4. **自动命名**: 如果不指定名称,会自动从URL推断

## 🎯 示例场景

### 场景1: 快速安装官方skill

1. 打开Skill管理器
2. 点击"📚 浏览仓库"
3. 切换到"Anthropic官方Skills"选项卡
4. 双击"example-skill"
5. 自动填充URL,点击下载

### 场景2: 浏览社区skills

1. 点击"📚 浏览仓库"
2. 切换到"Community Skills Hub"选项卡
3. 查看可用的skills列表
4. 选择感兴趣的skill
5. 点击"下载选中的Skill"

## 🌟 未来计划

- [ ] 支持在线搜索skills
- [ ] 支持用户添加自定义仓库源
- [ ] 显示skill的评分和下载量
- [ ] 支持skill的依赖关系
- [ ] 自动更新仓库列表

---

**享受使用Skill管理器! 🚀**