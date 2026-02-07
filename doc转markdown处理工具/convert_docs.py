import os
import subprocess
import re
from datetime import datetime

# 设置路径
PROJECT_ROOT = "/Users/yangjie/code/antigravity/doc转markdown处理工具"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "markdown")
LOG_FILE = os.path.join(PROJECT_ROOT, "log/debug.log")
DESC_SUMMARY_FILE = os.path.join(PROJECT_ROOT, "markdown/图表描述汇总.md")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] DEBUG: {message}\n")
    print(f"[{timestamp}] {message}")

def convert_grid_table_to_pipe(content):
    """
    尝试将 Pandoc 的 Grid Table 转换为标准的 Pipe Table。
    处理逻辑：识别 +---+ 组成的块，提取行，合并多行单元格，转为管道格式。
    """
    # 匹配 Grid Table 的正则表达式
    table_pattern = re.compile(r'(\n\+[-+]+\+\n.*?(\n\+[-+]+\+\n))', re.DOTALL)
    
    def table_replacer(match):
        full_table = match.group(1).strip()
        lines = full_table.split('\n')
        if not lines: return match.group(0)
        
        # 解析列宽和边界
        border_pattern = lines[0]
        col_indices = [i for i, char in enumerate(border_pattern) if char == '+']
        
        # 提取数据行
        rows = []
        current_row_data = [""] * (len(col_indices) - 1)
        
        for i in range(1, len(lines)):
            line = lines[i]
            if line.startswith('+'):
                if any(cell.strip() for cell in current_row_data):
                    rows.append([c.strip().replace('\n', ' ') for c in current_row_data])
                current_row_data = [""] * (len(col_indices) - 1)
                continue
            
            for j in range(len(col_indices) - 1):
                start = col_indices[j]
                end = col_indices[j+1]
                if start + 1 < len(line):
                    cell_content = line[start+1:end].rstrip()
                    cell_content = re.sub(r'^>\s*', '', cell_content).strip()
                    if cell_content:
                        if current_row_data[j]:
                            current_row_data[j] += " " + cell_content
                        else:
                            current_row_data[j] = cell_content
        
        if not rows: return match.group(0)
            
        # 生成 Pipe Table
        header = rows[0]
        pipe_table = "| " + " | ".join(header) + " |\n"
        pipe_table += "| " + " | ".join([":---"] * len(header)) + " |\n"
        for row in rows[1:]:
            row += [""] * (len(header) - len(row))
            pipe_table += "| " + " | ".join(row) + " |\n"
        return "\n" + pipe_table + "\n"

    new_content = table_pattern.sub(table_replacer, content)
    new_content = re.sub(r'\n\+[-+]+\+\n', '\n', new_content)
    return new_content

def refine_content(text):
    """
    后处理内容：
    1. 转换 Unicode 下标/上标。
    2. 修复中文加粗间的额外空格。
    3. 转换常用单位和公式为 LaTeX。
    4. 转换表格格式。
    """
    # 移除冗余锚点
    text = re.sub(r'\[\]\{#bookmark\d+\s+\.anchor\}', '', text)

    # 移除行首的误识别引用号 >
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_lines.append(re.sub(r'^>\s*', '', line))
    text = '\n'.join(cleaned_lines)

    # 替换 Unicode 下标
    sub_map = {
        '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
        '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9',
        'ₐ': 'a', 'ₑ': 'e', 'ₕ': 'h', 'ᵢ': 'i', 'ⱼ': 'j',
        'ₖ': 'k', 'ₗ': 'l', 'ₘ': 'm', 'ₙ': 'n', 'ₒ': 'o',
        'ₚ': 'p', 'ᵣ': 'r', 'ₛ': 's', 'ₜ': 't', 'ᵤ': 'u', 'ᵥ': 'v', 'ₓ': 'x'
    }
    for char, replacement in sub_map.items():
        text = text.replace(char, f"$_{{{replacement}}}$")
    
    # 替换 Unicode 上标
    sup_map = {
        '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4',
        '⁵': '5', '⁶': '6', '⁷': '7', '⁸': '8', '⁹': '9'
    }
    for char, replacement in sup_map.items():
        text = text.replace(char, f"$^{{{replacement}}}$")

    # 修复中文加粗间的额外空格
    for _ in range(5):
        text = re.sub(r'\*\*\s*([\u4e00-\u9fa5]+)\s*\*\*\s*\*\*\s*([\u4e00-\u9fa5]+)\s*\*\*', r'**\1\2**', text)
    
    # 清理加粗内的空格
    text = re.sub(r'\*\*\s+([^\*]+?)\s+\*\*', r'**\1**', text)
    
    # 转换常用单位
    text = text.replace("W/m^{2}", "$W/m^2$")
    text = text.replace("MJ/m^{2}", "$MJ/m^2$")
    text = text.replace("kWh/m^{2}", "$kWh/m^2$")
    text = text.replace("m/s", "$m/s$")
    
    # 转换表格
    text = convert_grid_table_to_pipe(text)
    
    return text

def extract_descriptions(text):
    """
    提取图表描述，排除掉包含表格边框的干扰项。
    """
    clean_text = text.replace("**", "")
    # 排除包含 +--- 的行
    pattern = r'(?:^|\n)>?\s*(图|表)\s*(\d+[\.\- ]?\d*)\s*([^\+\-\n]+)'
    matches = re.findall(pattern, clean_text)
    
    results = []
    seen = set()
    for m in matches:
        label = m[0]
        num = m[1].strip()
        desc = m[2].strip()
        if desc and len(desc) > 2:
            entry = f"{label} {num} {desc}"
            if entry not in seen:
                results.append(entry)
                seen.add(entry)
            
    return results

def convert_file(file_path):
    base_name = os.path.basename(file_path)
    filename_no_ext = os.path.splitext(base_name)[0]
    output_path = os.path.join(OUTPUT_DIR, f"{filename_no_ext}.md")
    media_dir = os.path.join(OUTPUT_DIR, "media", filename_no_ext)
    
    log(f"正在转换文件: {base_name}")
    
    cmd = [
        "pandoc",
        "-f", "docx",
        "-t", "markdown",
        "--extract-media", media_dir,
        file_path,
        "-o", output_path
    ]
    
    try:
        subprocess.run(cmd, check=True)
        
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        content = refine_content(content)
        
        # 针对特定文件的定制优化
        if "太阳能资源年景评估技术规范" in filename_no_ext:
            # 1. 彻底碎片化日期和数字修复 (例如 2 0 2 4 -> 2024)
            # 处理多空格情况
            for _ in range(5):
                content = re.sub(r'(\d)\s+(\d)', r'\1\2', content)
                content = re.sub(r'(\d)\s*-\s*(\d)', r'\1-\2', content)

            # 2. 提取并格式化元数据
            # 优先查找类似 2023-10-18 的日期
            dates = re.findall(r'\d{4}-\d{1,2}-\d{1,2}', content)
            pub_date = dates[0] if len(dates) > 0 else "2023-10-18"
            imp_date = dates[1] if len(dates) > 1 else "2024-02-01"
            
            # 3. 彻底移除旧标题和干扰行
            # 增加对无意义图片行和元数据行的清理
            content = re.sub(r'(?m)^.*(width|height|image|QX/T|ICS|中华人民共和国|发布|实施|中国气象局).*$', '', content)
            
            # 构建标准头部 (使用 \n\n 确保 Markdown 换行)
            header = [
                "# 太阳能资源年景评估技术规范",
                "**QX/T 683—2023**",
                "**ICS 07.060 CCS A 47**",
                "**中华人民共和国气象行业标准**",
                f"**发布日期：{pub_date}**",
                f"**实施日期：{imp_date}**",
                "**中国气象局 发布**",
                "---"
            ]
            
            # 4. 重新组合
            content = "\n\n".join(header) + "\n\n" + content
            
            # 修复前言和正文之间的诡异粘连 (针对 L43)
            # 匹配模式：起草人...**太阳能资源年景评估技术规范**1**范围**
            content = re.sub(r'(本文件主要起草人：[^\*]+)。\*\*太阳能资源年景评估技术规范\*\*1\*\*范围\*\*', r'\1。\n\n## 1 范围\n\n', content)
            
            # 通用的标题粘连修复 (防止上面的特定规则没匹配到)
            content = re.sub(r'\*\*(范围|规范性引用文件)\*\*', r'\n\n## 1 \1\n\n', content)
            
            # 5. 修复章节标题 (采用白名单防止误判单词)
            def heading_fixer(match):
                num = match.group(1).strip()
                title = match.group(2).strip()
                whitelist = ["范围", "规范性引用文件", "术语和定义", "数据收集和处理", "年景评估方法", "年景评估内容及结果", "证实方法"]
                if title in whitelist:
                    return f"\n\n\n## {num} {title}\n\n\n"
                return match.group(0)
            
            content = re.sub(r'\*\*([\d\.]+)\*\*\s*\*\*([^\s\*]+)\*\*', heading_fixer, content)
            
            # 使用更强大的正则处理目次及其条目
            content = re.sub(r'(?:\*\*|)\s*目次\s*(?:\*\*|)\s*\[前言', r'\n\n\n## 目次\n\n- [前言', content)

            # 修复前言为 H2
            content = content.replace("# 前言", "## 前言")
            content = content.replace("**前言**", "\n\n\n## 前言\n\n\n")
            # 给目次后续项添加列表符 (匹配格式如 [数字 范围/标题等 任意])
            # 改进正则以匹配更多情况
            content = re.sub(r'(?m)^\[([\d\.]+)\s+([^\s]+?)\s+\d+\]', r'- [\1 \2]', content)
            # 处理加粗的目录项
            content = re.sub(r'(?m)^\*\*\[(\d+)\s+([^\s]+?)\s+\d+\]\*\*', r'- [\1 \2]', content)
            
            # 5. 针对表格中的公式进行特殊处理
            content = content.replace("---20<GHR", "$-20 < GHR$")
            content = content.replace("GHRp≤-100", "$GHR_p \\le -100$")

        if "新型能源体系建设中的气象问题与技术进展" in filename_no_ext:
            # 1. 强力移除标题前的所有杂质 (包括乱码表格、引用行、年份等)
            
            # 先手动清除特定的连续乱码行
            content = re.sub(r'^\:\+.*?\n', '', content)
            content = re.sub(r'(?m)^\|.*\|$', '', content)
            content = re.sub(r'(?s)^.*?SHEN Yanbo\. Meteorological issues and technological.*?\n', '', content)
            content = re.sub(r'(?s)^.*?，2025，12（1）：31-42\.', '', content)
            content = re.sub(r'(?m)^.*: 31-42\.$', '', content)
            content = re.sub(r'(?m)^.*height=.*$', '', content)
            content = re.sub(r'^SHEN Yanbo\. Meteorological issues.*?\n', '', content, flags=re.MULTILINE)
            
            # 手动清理特定乱码图片行
            content = re.sub(r'!\[\].*?\{width="0.45.*?\n', '', content)
            content = content.replace("论文二维码", "")

            # 2. 提取并格式化标题
            content = re.sub(r'新型能源体系建设中的气象问题与技术进展\n\n申彦波', r'# 新型能源体系建设中的气象问题与技术进展\n\n**申彦波**', content)
            
            # 3. 格式化作者单位
            content = content.replace("（ 1. 中国气象局", "\n\n（1. 中国气象局")
            content = content.replace("2. 中国气象局", "\n2. 中国气象局")
            
            # 4. 格式化摘要和关键词
            content = content.replace("摘要：", "\n\n**摘要：**")
            content = content.replace("关键词：", "\n\n**关键词：**")
            content = content.replace("SDP**DOI**：", "SDP\n\n**DOI**：")  # 修复粘连
            
            # 5. 格式化英文部分
            content = content.replace("**Meteorological Issues", "\n\n**Meteorological Issues")
            content = content.replace("Systems**SHEN Yanbo", "Systems**\n\nSHEN Yanbo")
            content = content.replace("China）**Abstract:**", "China）\n\n**Abstract:**")
            
            # 修复 Key words
            content = content.replace("**Key words:**new", "\n\n**Key words:** new")
            content = re.sub(r'SDP\*\*2095-8676\*\*', 'SDP', content)
            content = content.replace("**2095-8676**", "")
            
            # 6. 元数据后置处理
            content = re.sub(r'(收稿日期：.*?)\n', r'> \1\n\n', content)
            content = re.sub(r'(基金项目：.*?)\n', r'> \1', content) # 移除换行，尝试粘连
            content = re.sub(r'> (基金项目：.*?) "\n\n', r'> \1 "', content) # 针对特定断行修复
            
            # 7. 清理多余空行
            content = re.sub(r'\n{4,}', '\n\n', content)
            
            # 8. 最后一道防线：移除标题前的所有非空行
            if "# 新型能源体系" in content:
                 content = content[content.find("# 新型能源体系"):]

        if "中国风能太阳能资源年景公报" in filename_no_ext:
            # 1. 强力移除头部所有 width= 行
            content = re.sub(r'(?m)^.*?\{width=.*?\}.*?$', '', content)
            
            # 手动构建头部
            year = "2023"
            if "2024" in filename_no_ext:
                 year = "2024"
            
            publish_date = f"{int(year)+1} 年 2 月"
            
            # 完整标题块
            header_block = f"""# CHINA WIND AND SOLAR ENERGY RESOURCES BULLETIN

# 中国风能太阳能资源年景公报（{year} 年）

**中国气象局风能太阳能中心**

**{publish_date}**

"""
            # 2. 截取内容并替换头部
            # 手动构建头文字符串
            header_str = f"# CHINA WIND AND SOLAR ENERGY RESOURCES BULLETIN\n\n# 中国风能太阳能资源年景公报（{year} 年）\n\n**中国气象局风能太阳能中心**\n\n**{publish_date}**\n\n"

            idx = content.find("**摘要**")
            if idx != -1:
                # 无论摘要前面有什么（包括换行符或乱码），全部扔掉
                # 直接拼接新头 + 摘要部分
                content = header_str + content[idx:]
            elif "**一、风能资源**" in content:
                idx = content.find("**一、风能资源**")
                # 如果只有正文开始，补一个摘要头
                content = header_str + "**摘要**\n\n01\n\n" + content[idx:]
            else:
                 # 兜底：如果实在找不到锚点，尝试暴力正则替换开头的乱码标题
                 if content.strip().startswith("# （"):
                     content = re.sub(r'^# （.*?）\s*', header_str, content, count=1)
                 else:
                     content = header_str + content.lstrip()
            
            # 4. 移除页眉页脚干扰 (排除标题栏)
            content = re.sub(r'(?m)^(?!#).*HINA WIND A.*$', '', content)
            content = re.sub(r'(?m)^(?!#).*D SOLAR ENERGY RESOURCES BULLETIN.*$', '', content)
            
            # 5. 移除不必要的空行
            content = re.sub(r'\n{4,}', '\n\n', content)

        descriptions = extract_descriptions(content)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        log(f"文件处理完成: {base_name}，提取到 {len(descriptions)} 个描述")
        return descriptions
    except Exception as e:
        log(f"转换失败 {base_name}: {str(e)}")
        return []

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    files = sorted([f for f in os.listdir(DOCS_DIR) if f.endswith(".docx")])
    log(f"找到 {len(files)} 个待处理文件")
    
    all_descs = []
    for f in files:
        descs = convert_file(os.path.join(DOCS_DIR, f))
        if descs:
            all_descs.append(f"### {f}\n- " + "\n- ".join(descs))
            
    with open(DESC_SUMMARY_FILE, "s", encoding="utf-8") if 's' == 'w' else open(DESC_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("# 图表描述汇总\n\n本文件汇总了所有转换文档中的图表标题描述。\n\n")
        f.write("\n\n".join(all_descs))
        
    log(f"汇总文件已重新生成: {DESC_SUMMARY_FILE}")

if __name__ == "__main__":
    main()

