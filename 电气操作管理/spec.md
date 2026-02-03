# 操作票汇总整理项目 (Operation Tickets Consolidation) Spec

## 1. 构架与选型 (Architecture & Selection)

- **核心工具**: Python 3.10+
- **关键库**:
  - `python-docx`: 用于解析 `.docx` 文件中的表格内容。
  - `pandas`: 用于数据处理和整合。
  - `openpyxl`: 用于生成 `.xlsx` 文件。
  - `textutil` (MacOS 内置): 用于将旧版的 `.doc` 文件转换为 `.docx` 格式。

## 2. 资料模型 (Data Model)

汇总后的 Excel 表格结构如下：
| 字段名 | 说明 |
| :--- | :--- |
| **所属站场** | 对应所在的文件夹名称（如：坤山风电场） |
| **文件名称** | 原始文件名 |
| **操作任务** | 从操作票中提取的“操作任务”字段 |
| **顺序** | 操作步骤的序号 |
| **操作项目** | 具体的步骤内容 |
| **完成时间** | 操作票中记录的步骤完成时间（通常为空白） |

## 3. 关键流程 (Key Workflow)

1. **环境准备**: 检查并安装必要的 Python 依赖。
2. **格式转换**: 遍历目录，将所有 `.doc` 文件转换为 `.docx`。
3. **数据提取**: 递归遍历子目录，解析每个 `.docx` 文件的表格：
   - 定位包含“顺序”和“操作项目”的表格。
   - 提取“操作任务”信息。
   - 逐行提取操作步骤。
4. **数据清洗**: 去除重复项、空白行，合并单元格数据。
5. **汇总输出**: 将所有提取的数据写入一个 Excel 文件。

## 4. 虚拟码 (Pseudocode)

```python
Initialize list for all_tickets
Walk through directory:
    If file is .doc, convert to .docx
    If file is .docx:
        Open document
        station_name = parent_folder
        file_name = current_filename
        task_name = ""
        For table in doc.tables:
            If "操作任务" in table.cell(0,0).text and table.rows > 5:
                # This is likely the steps table
                task_name = find_task_name(table)
                For row in rows_after_header:
                    order = row.cells[2].text
                    task_item = row.cells[3].text
                    finish_time = row.cells[8].text
                    Append to all_tickets
Create DataFrame and Save to "操作票汇总表.xlsx"
```
