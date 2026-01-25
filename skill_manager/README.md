# Skill管理器

一个功能完善的Skill管理工具,支持skill的安装、卸载、下载和管理,提供图形界面和命令行两种使用方式。

## ✨ 功能特性

- 📦 **安装Skill** - 从本地路径安装skill
- 🗑️ **卸载Skill** - 移除已安装的skill
- 📥 **下载Skill** - 从Git仓库或ZIP文件下载并安装
- 📋 **列表管理** - 查看所有已安装的skills
- 🔍 **详情查看** - 查看skill的详细信息
- 💾 **配置持久化** - 自动保存skill配置信息
- 🖥️ **图形界面** - 友好的GUI操作界面
- ⌨️ **命令行支持** - 支持命令行操作(待实现)

## 📦 安装

无需额外安装,直接使用即可。

### 依赖

- Python 3.7+
- tkinter (通常Python自带)
- Git (可选,用于从Git仓库下载)

## 🚀 快速开始

### 使用GUI界面

```bash
python3 skill_manager_gui.py
```

启动后你将看到:
- **下载Skill区域** - 输入URL下载skill
- **Skills列表** - 显示所有已安装的skills
- **操作按钮** - 刷新、安装、卸载、查看详情
- **操作日志** - 实时显示操作信息

### 使用Python代码

```python
from skill_manager import SkillManager

# 创建管理器实例
manager = SkillManager()

# 列出所有skills
skills = manager.list_skills()
for skill in skills:
    print(f"{skill['name']}: {skill['description']}")

# 从本地安装skill
success, msg = manager.install_skill('/path/to/skill', 'my-skill')
print(msg)

# 从Git仓库下载skill
success, msg = manager.download_skill(
    'https://github.com/username/skill-repo.git', 
    'my-skill'
)
print(msg)

# 从ZIP文件下载skill
success, msg = manager.download_skill(
    'https://example.com/skill.zip', 
    'my-skill'
)
print(msg)

# 卸载skill
success, msg = manager.uninstall_skill('my-skill')
print(msg)

# 获取skill信息
info = manager.get_skill_info('my-skill')
if info:
    print(f"版本: {info['version']}")
    print(f"描述: {info['description']}")
```

## 📖 使用指南

### 1. 下载Skill

#### 从Git仓库下载

1. 在URL输入框中输入Git仓库地址
2. (可选)在名称输入框中指定skill名称
3. 点击"下载"按钮

支持的Git URL格式:
- `https://github.com/username/repo.git`
- `https://github.com/username/repo`
- `https://gitlab.com/username/repo.git`

#### 从ZIP文件下载

1. 在URL输入框中输入ZIP文件地址
2. (可选)在名称输入框中指定skill名称
3. 点击"下载"按钮

示例:
- `https://example.com/skill.zip`
- `https://github.com/username/repo/archive/refs/heads/main.zip`

### 2. 安装本地Skill

1. 点击"安装本地Skill"按钮
2. 选择skill所在的文件夹
3. 确认安装

### 3. 卸载Skill

1. 在列表中选择要卸载的skill
2. 点击"卸载选中"按钮
3. 确认卸载

### 4. 查看Skill详情

1. 在列表中选择一个skill
2. 点击"查看详情"按钮
3. 在弹出窗口中查看详细信息

## 📁 Skill结构

一个标准的skill目录结构:

```
my-skill/
├── skill.json          # skill配置文件(可选)
├── main.py            # 主程序文件
├── README.md          # 说明文档
└── ...                # 其他文件
```

### skill.json 示例

```json
{
  "name": "my-skill",
  "version": "1.0.0",
  "description": "这是我的skill",
  "author": "Your Name",
  "dependencies": []
}
```

如果没有 `skill.json`,也可以使用 `package.json` 或 `config.json`。

## 🗂️ 目录结构

```
skill_manager/
├── skill_manager.py      # 核心管理模块
├── skill_manager_gui.py  # GUI界面
├── README.md            # 本文档
└── skills/              # skills存储目录(自动创建)
    ├── skills_config.json  # 配置文件
    ├── skill1/          # 已安装的skill
    └── skill2/          # 已安装的skill
```

## 🔧 配置文件

Skill管理器会在 `skills/` 目录下创建 `skills_config.json` 文件:

```json
{
  "installed_skills": {
    "my-skill": {
      "version": "1.0.0",
      "description": "我的第一个skill",
      "author": "Your Name",
      "installed_at": "2026-01-25T13:00:00",
      "source": "/path/to/original/skill"
    }
  },
  "repositories": []
}
```

## 💡 使用示例

### 示例1: 从GitHub下载skill

```python
from skill_manager import SkillManager

manager = SkillManager()

# 下载一个GitHub上的skill
success, msg = manager.download_skill(
    'https://github.com/example/awesome-skill.git'
)

if success:
    print("✅", msg)
    # 查看已安装的skills
    skills = manager.list_skills()
    for skill in skills:
        print(f"📦 {skill['name']} v{skill['version']}")
else:
    print("❌", msg)
```

### 示例2: 本地开发和安装

```bash
# 创建skill目录
mkdir my-new-skill
cd my-new-skill

# 创建skill文件
echo '{"name": "my-new-skill", "version": "1.0.0", "description": "My awesome skill"}' > skill.json
echo 'print("Hello from my skill!")' > main.py

# 使用GUI安装
# 1. 启动GUI: python3 skill_manager_gui.py
# 2. 点击"安装本地Skill"
# 3. 选择 my-new-skill 文件夹
```

## ⚙️ API参考

### SkillManager类

#### `__init__(skills_dir=None)`
初始化Skill管理器

**参数**:
- `skills_dir`: skills存储目录,默认为当前目录下的skills文件夹

#### `list_skills() -> List[Dict]`
列出所有已安装的skills

**返回**: skill信息列表

#### `install_skill(skill_path, skill_name=None, force=False) -> tuple[bool, str]`
安装skill(从本地路径)

**参数**:
- `skill_path`: skill的本地路径
- `skill_name`: skill名称,如果不指定则使用文件夹名
- `force`: 是否强制覆盖已存在的skill

**返回**: (是否成功, 消息)

#### `download_skill(url, skill_name=None, progress_callback=None) -> tuple[bool, str]`
从URL下载并安装skill

**参数**:
- `url`: skill的下载URL (支持.zip文件或git仓库)
- `skill_name`: skill名称,如果不指定则自动推断
- `progress_callback`: 进度回调函数 callback(message: str)

**返回**: (是否成功, 消息)

#### `uninstall_skill(skill_name) -> tuple[bool, str]`
卸载skill

**参数**:
- `skill_name`: skill名称

**返回**: (是否成功, 消息)

#### `get_skill_info(skill_name) -> Optional[Dict]`
获取指定skill的详细信息

**参数**:
- `skill_name`: skill名称

**返回**: skill信息,如果不存在返回None

## ❓ 常见问题

### Q: 如何创建一个skill?

A: 创建一个文件夹,添加你的代码文件,可选添加 `skill.json` 配置文件,然后使用GUI或代码安装。

### Q: 下载失败怎么办?

A: 检查:
1. 网络连接是否正常
2. URL是否正确
3. Git是否已安装(如果下载Git仓库)
4. 查看操作日志中的详细错误信息

### Q: 如何更新已安装的skill?

A: 重新下载或安装,会自动覆盖旧版本。

### Q: skills存储在哪里?

A: 默认存储在当前目录的 `skills/` 文件夹中。

### Q: 可以同时安装多个版本的同一个skill吗?

A: 不可以,同一个名称的skill只能安装一个版本。如需多版本,请使用不同的skill名称。

## 🛠️ 开发计划

- [ ] 命令行界面支持
- [ ] Skill依赖管理
- [ ] Skill仓库源管理
- [ ] Skill搜索功能
- [ ] Skill更新检查
- [ ] 批量操作支持

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request!

---

**Made with ❤️ by Skill Manager Team**

## 需完善：

1. 描述显示中文 (已实现)
2. 增加自动连接翻译网站自动翻译形成翻译库功能（已实现）
3. agent skill市场 https://skillsmp.com/zh ❌取消
4. 添加仓库功能 （已实现）
5. 主页面搜索功能