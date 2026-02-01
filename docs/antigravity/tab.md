# Antigravity 编辑器：标签页与导航 (Tab & Navigation)

本指南涵盖了核心导航和补全工具：Supercomplete、Tab-to-Jump 和 Tab-to-Import。

## Supercomplete

Supercomplete 在当前光标位置附近的区域提供代码建议。

### 工作原理

* **全文件建议**：建议可以修改整个文档中的代码，同时处理诸如更改变量名或更新单独的函数定义等任务。
* **接受**：按 Tab 键接受更改。

## Tab-to-Jump

Tab-to-Jump 是一种流体导航工具，它会建议文档中下一个逻辑位置，以便您移动光标。

### 工作原理

* 会出现一个 "Tab to jump" 图标，提议将光标移至下一个逻辑编辑位置。按下 Tab 键可立即将光标移至该位置。
* **接受**：按 Tab 键接受跳转。

## Tab-to-Import

Tab-to-Import 可以在不中断流程的情况下处理缺失的依赖项。

### 工作原理

* **检测**：如果您输入了一个未导入的类或函数，Antigravity 会建议导入。
* **操作**：按 Tab 键完成单词，并立即在文件顶部添加导入语句。

## 设置 (Settings)

在设置中，您可以自定义这些特性的行为：

* **启用/禁用特性**：您可以分别关闭 Autocomplete、Tab-to-Jump、Supercomplete 或 Tab-to-Import。
* **Tab 速度**：控制建议的响应速度（Slow, Default, Fast）。
* **突出显示插入文本**：启用后，通过 Tab 插入的文本将被突出显示，以便轻松跟踪更改。
* **剪贴板上下文**：启用后，Antigravity 将使用剪贴板内容来提高补全准确性。
* **允许 Gitignored 文件**：在 `.gitignore` 列出的文件中启用 Tab 功能。
