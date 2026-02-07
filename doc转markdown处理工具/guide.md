# 文档转换工具使用说明书 (guide.md)

## 1. 功能概述

本工具通过 Python 脚本自动化调用 Pandoc，将 `docs/` 目录下的 `.docx` 文档转换为 Markdown 格式，并进行了一系列后处理以提升可读性和专业度。

## 2. 转换特性

- **公式转换**: 自动识别 Unicode 下标/上标、MathML 等并映射为标准 LaTeX 格式。
- **表格还原**: 完美还原 Word 表格为 Markdown 表格（Grid Table 或 Pipe Table）。
- **图片提取**: 自动提取文档内的图片至 `markdown/media/{文件名}/` 目录，并在 MD 中正确引用。
- **描述提取**: 自动扫描并提取文中所有“图 x-x”及“表 x-x”开头的描述，汇总至 `图表描述汇总.md`。
- **文本清洗**: 自动修复 Pandoc 转换中文时常见的文本间空格、加粗标签冗余等问题。

## 3. 使用方法

### 环境要求

- 已安装 Pandoc (建议 v3.0+)
- 已安装 Python 3

### 执行命令

在项目根目录下运行一键转换脚本：

```bash
python3 run_all.py
```

该脚本将自动执行：

1. **convert_docs.py**: 调用 Pandoc 并执行基础排版。
2. **clean_markdown.py**: 执行深度段落合并与排版清洗。
3. **final_polish.py**: 最终细节润色并核对信息完整性。

## 4. 输出说明

- **markdown/**: 转换后的 MD 文件。
- **markdown/media/**: 提取的图片资源。
- **markdown/图表描述汇总.md**: 所有文档图表标题的索引汇总。

## 5. 注意事项

- 若文档中公式极其复杂（如非标准公式对象），建议手动校验生成的 LaTeX。
- 图片分辨率取决于原始 Docx 文件中的嵌入质量。
