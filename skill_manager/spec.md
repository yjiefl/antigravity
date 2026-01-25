# Skill管理器 - 搜索功能设计文档 (spec.md)

## 1. 架构与选型
- **前端**: Python Tkinter (现有架构)
- **后端**: SkillManager (现有架构)
- **搜索机制**: 内存中过滤。将所有已安装的 Skill 加载到内存列表中，根据用户输入的关键词进行实时过滤。

## 2. 资料模型
搜索功能涉及到的主要数据模型是 Skill 信息对象：
```python
{
    "name": str,            # Skill 名称
    "version": str,         # 版本号
    "description": str,     # 英文描述
    "description_zh": str,  # 中文描述
    "path": str,            # 本地路径
    "source": str           # 来源 URL
}
```

## 3. 关键流程
### 搜索流程
1. 用户在搜索框输入文字。
2. 触发 `KeyRelease` 事件。
3. 获取输入框内容 `query`。
4. 遍历 `self.all_skills` 列表。
5. 匹配条件：
   - `query` 是否在 `name` 中（忽略大小写）。
   - `query` 是否在 `description` 或 `description_zh` 中（忽略大小写）。
6. 更新 `ttk.Treeview` 显示过滤后的结果。

## 4. Mermaid 图表

### 4.1 系统脉络图
```mermaid
graph TD
    User([用户]) --> GUI[Skill管理器 GUI]
    GUI --> SM[SkillManager 核心]
    SM --> FS[文件系统/Skills目录]
    SM --> SL[skill_translations.json]
```

### 4.2 搜索流程图
```mermaid
flowchart TD
    A[开始] --> B[监听搜索框输入]
    B --> C{输入非空?}
    C -- 是 --> D[遍历所有 Skill]
    C -- 否 --> E[显示完整列表]
    D --> F{匹配名称或内容?}
    F -- 是 --> G[加入结果集]
    F -- 否 --> H[跳过]
    G --> I[更新 UI 列表]
    H --> D
    E --> I
    I --> J[结束]
```

### 4.3 序列图
```mermaid
sequenceDiagram
    participant User as 用户
    participant GUI as SkillManagerGUI
    participant SM as SkillManager
    
    User->>GUI: 输入搜索关键词
    GUI->>GUI: 触发 search_skills()
    Note over GUI: 在 self.all_skills 中过滤
    GUI->>GUI: refresh_treeview(filtered_list)
    GUI-->>User: 显示过滤结果
```

## 5. 虚拟码
```python
def on_search_change(query):
    query = query.lower()
    filtered_results = []
    for skill in all_skills:
        name_match = query in skill.name.lower()
        desc_match = query in skill.description.lower() or query in skill.description_zh.lower()
        if name_match or desc_match:
            filtered_results.append(skill)
    update_treeview(filtered_results)
```

## 6. 模组关系图
```mermaid
classDiagram
    class SkillManagerGUI {
        +all_skills: list
        +search_entry: Entry
        +create_search_section()
        +on_search_key_release()
        +refresh_skills()
    }
    class SkillManager {
        +list_skills(): list
        +get_skill_info(): dict
    }
    SkillManagerGUI --> SkillManager
```
