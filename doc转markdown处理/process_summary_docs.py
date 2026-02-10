import os
import subprocess
import re
import shutil
from datetime import datetime

# 设置路径
PROJECT_ROOT = "/Users/yangjie/code/antigravity/doc转markdown处理工具"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs/2025-2026 总结汇总")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "markdown/2025-2026 总结汇总")
LOG_FILE = os.path.join(PROJECT_ROOT, "log/debug_summary.log")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] DEBUG: {message}\n")
    print(f"[{timestamp}] {message}")

# --- From convert_docs.py ---

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

# --- From clean_markdown.py ---

def clean_markdown_content(content):
    # 1. 移除 bookmark 锚点
    content = re.sub(r'\[\]\{#bookmark\d+\s+\.anchor\}', '', content)
    
    # 2. 移除行首和行尾的误识别引用号 >
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        l = line.strip()
        # 移除行首的 >
        l = re.sub(r'^>\s*', '', l)
        # 移除行尾的 > (常见于段落末尾误连)
        l = re.sub(r'\s*>$', '', l)
        cleaned_lines.append(l)
    content = '\n'.join(cleaned_lines)

    # 3. 修复中文加粗间的额外空格
    for _ in range(5):
        content = re.sub(r'\*\*\s*([\u4e00-\u9fa5]+)\s*\*\*\s*\*\*\s*([\u4e00-\u9fa5]+)\s*\*\*', r'**\1\2**', content)
    
    def clean_bold_internal(match):
        inner = match.group(1)
        if re.match(r'^[\u4e00-\u9fa5\s]+$', inner):
            return f"**{inner.replace(' ', '')}**"
        return match.group(0)
    content = re.sub(r'\*\*(.+?)\*\*', clean_bold_internal, content)

    # 4. 智能合并段落
    final_paragraphs = []
    # 按双换行符分割段落
    raw_paras = content.split('\n\n')
    for rp in raw_paras:
        if not rp.strip(): continue
        
        # 排除表格和列表
        if rp.strip().startswith('|') or rp.strip().startswith('+') or rp.strip().startswith('- ') or rp.strip().startswith('* '):
            final_paragraphs.append(rp)
            continue
            
        lines = rp.split('\n')
        merged_para = ""
        for i, line in enumerate(lines):
            line = line.strip()
            if not line: continue
            
            if merged_para == "":
                merged_para = line
            else:
                # 判断是否需要加空格
                # 如果前一行以汉字结尾，下一行以汉字开头，不加空格
                # 否则（如英文，或标点后）加空格
                last_char = merged_para[-1]
                first_char = line[0]
                
                is_last_cjk = re.match(r'[\u4e00-\u9fa5，。？！；：]', last_char)
                is_first_cjk = re.match(r'[\u4e00-\u9fa5]', first_char)
                
                if is_last_cjk and is_first_cjk:
                    merged_para += line
                else:
                    merged_para += " " + line
        
        # 清理合并后段落内的多余空格
        merged_para = re.sub(r'(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])', '', merged_para)
        final_paragraphs.append(merged_para)
        
    content = '\n\n'.join(final_paragraphs)

    # 5. 移除特定重复出现的杂质
    junk_strings = [
        r'南方能源建设', r'Vol\.\s*\d+ No\.\s*\d+', r'January \d{4}',
        r'SOUTHERN ENERGY CONSTRUCTION',
        r'CSTR\s*[:：]\s*[0-9\.]+',
        r'DOI\s*[:：]\s*.*?\s', # 只匹配到空格或换行
        r'中图分类号\s*[:：]\s*.*?[\s\n]',
        r'文章编号\s*[:：]\s*.*?\s',
        r'© \d{4} Energy China GEDI.*',
        r'This is an open access article under the CC BY-NC license.*'
    ]
    for pattern in junk_strings:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    # 7. 移除损坏的表格伪迹和修复断行
    # 移除像 +- ---+ 这种残留在文本或表格中的边框线
    content = re.sub(r'\+[- ]+[\+\-| ]+', '', content)
    
    # 修复被 > 或空格或 | 拆分的数字 (如 20 > 000, 15 | 000)
    # 处理 > 和 | 分隔
    content = re.sub(r'(\d)\s*[>\|]\s*(\d)', r'\1\2', content)
    # 处理多空格分隔且看起来像万位分隔的情况
    content = re.sub(r'(\d)\s+(\d{3})(?!\d)', r'\1\2', content)

    # 修复被表格线或断行拆分的图片链接
    # 这种链接通常包含 ![](/...image...png)
    def fix_image_tags(match):
        inner = match.group(0)
        # 移除换行、列分隔符和多余空格
        cleaned = re.sub(r'[\n\|]', '', inner)
        cleaned = re.sub(r'\s{2,}', ' ', cleaned)
        return cleaned
    content = re.sub(r'\!\[\]\(.*?\)\{.*?\}', fix_image_tags, content, flags=re.DOTALL)

    # 识别并清理这种“单行长表格” (通常是图表标签误提取)
    def clean_monster_line(match):
        line = match.group(0)
        # 如果一行包含太多的 | 且不是真正的表格结构
        if line.count('|') > 6:
            # 移除所有 | 和 >，转为普通文本
            new_line = line.replace('|', ' ').replace('>', ' ')
            new_line = re.sub(r'\s{2,}', ' ', new_line).strip()
            return "\n\n\n" + new_line + "\n\n\n"
        return match.group(0)
    
    content = re.sub(r'(?m)^\|.*\|$', clean_monster_line, content)

    # 移除孤立的表格分隔符行 (如 | :--- | :--- |)
    content = re.sub(r'(?m)^\|[\s\-:\|]+\|[\s\n]*$', '', content)

    # 修复常见单位和关键词
    content = content.replace("me dia", "media")
    content = content.replace("i mage", "image")
    content = content.replace("c ode", "code")
    content = content.replace("15 000", "15000") 
    content = content.replace("M W", "MW")
    content = content.replace("/ MW", " / MW")
    content = content.replace("功 率", "功率")

    # 修复路径断词和路径中多余空格
    for _ in range(5):
        content = re.sub(r'(?<=/)\s+|(?<=\w)\s+(?=/)|(?<=/)\s+(?=\w)', '', content)
    
    # 针对已知路径关键字增强清理
    for kw in ['media', 'image', 'code', 'markdown', 'antigravity']:
        content = re.sub(r'\s+' + kw, kw, content)
        content = re.sub(kw + r'\s+', kw, content)

    # 清理行首尾的杂质
    content = re.sub(r'(?m)^[>\s\|]+$', '', content)
    
    # 移除行尾多余空格和冗余星号碎片 (如 ****)
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        l = line.rstrip()
        # 只移除 4 个或更多连续星号（通常是转换碎屑），保留 2 个星号（加粗）
        l = re.sub(r'\*{4,}$', '', l) 
        cleaned_lines.append(l)
    content = '\n'.join(cleaned_lines)
    
    content = re.sub(r'(?m)^\*+$', '', content) # 移除只有星号的行
    
    # 8. 统一单位转换
    content = content.replace(" kwh/m$^{2}$", " $kWh/m^2$")
    content = content.replace(" kWh/m$^{2}$", " $kWh/m^2$")
    content = content.replace(" W/m$^{2}$", " $W/m^2$")
    content = content.replace(" m/s", " $m/s$")
    
    # 9. 移除过多的空行
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    content = re.sub(r'\n{3}', '\n\n', content)

    # 10. 移除参考文献中的 DOI 链接和冗余信息
    content = re.sub(r'(?m)^\[[\d\.\-a-zA-Z]+\]\(https?://doi\.org/[^\)]+\)\.?\s*$', '', content)
    
    def clean_citation_link(match):
        text = match.group(1)
        url = match.group(2)
        dot = match.group(3)
        space = match.group(4)
        if text in url:
            if text.isdigit() and len(text) == 4 and 1900 <= int(text) <= 2030:
                pass 
            elif re.match(r'^[a-zA-Z0-9\.\-/_]+$', text) and any(c.isdigit() for c in text):
                return "" 
        return text + dot + space

    content = re.sub(r'\[([^\]]+)\]\((https?://doi\.org/[^\)]+)\)(\.?)(\s*)', clean_citation_link, content)
    
    return content

# --- From final_polish.py ---

def final_polish_content(content):
    # 移除行尾的冗余符号（如误导的 > 或多余空格）
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        l = line.rstrip()
        # 移除行尾的 > 或 >** 这种误识别
        l = re.sub(r'[>\s]+$', '', l)
        cleaned_lines.append(l)
    content = '\n'.join(cleaned_lines)
    
    # 修复加粗结束后紧跟文字没有空格的情况
    content = content.replace("**>", "** ")
    
    return content

def upgrade_headers(content):
    """
    将中文序号（一、 （一） 1. （1））转换为 Markdown 标题。
    假设第一行或已有 # 是 H1。
    一、 -> H2
    （一） -> H3
    1. / 1、 -> H4
    （1） -> Bold text or H5 (视情况，通常 H5 过深，建议加粗)
    """
    lines = content.split('\n')
    new_lines = []
    
    # 正则预编译
    p_h2 = re.compile(r'^[零一二三四五六七八九十]+、')
    p_h3 = re.compile(r'^[（(][零一二三四五六七八九十]+[）)]')
    p_h4 = re.compile(r'^\d+[.、]\s*') # 匹配 1. 或 1、
    p_h5 = re.compile(r'^[（(]\d+[）)]')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            new_lines.append(line)
            continue
            
        # 如果已经是标题，跳过
        if stripped.startswith('#'):
            new_lines.append(line)
            continue
            
        # 识别层级
        if p_h2.match(stripped):
            new_lines.append(f"## {stripped}")
        elif p_h3.match(stripped):
            new_lines.append(f"### {stripped}")
        elif p_h4.match(stripped):
            # 1. 这种可能是列表，也可能是标题。
            # 如果后面紧跟大量文字，可能是列表项。
            # 如果较短（<50字）且不以标点结尾，倾向于标题。
            if len(stripped) < 50 and not stripped.endswith(('。', '；')):
                 new_lines.append(f"#### {stripped}")
            else:
                 new_lines.append(line) # 保持原样（即 markdown 列表或文本）
        elif p_h5.match(stripped):
            # （1）通常作为小点，加粗即可，做成标题太深
            new_lines.append(f"**{stripped}**")
        else:
            new_lines.append(line)
            
    return '\n'.join(new_lines)


def convert_file(file_path):
    base_name = os.path.basename(file_path)
    filename_no_ext = os.path.splitext(base_name)[0]
    output_path = os.path.join(OUTPUT_DIR, f"{filename_no_ext}.md")
    media_dir = os.path.join(OUTPUT_DIR, "media", filename_no_ext)
    
    log(f"正在转换文件: {base_name}")
    
    # Create output directory
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Ensure media directory is clean/created
    os.makedirs(media_dir, exist_ok=True)
    
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
            
        # Pipeline: Refine -> Clean -> Polish -> Upgrade Headers
        content = refine_content(content)
        content = clean_markdown_content(content)
        content = final_polish_content(content)
        content = upgrade_headers(content)

        
        # Additional Step: Fix Image Paths
        # Pandoc extracts media to media_dir, but the links in markdown point to `media/filename/...`
        # We need to make sure the relative paths work. 
        # Since we put md files in `markdown/2025-2026 总结汇总/`, and media in `markdown/2025-2026 总结汇总/media/filename/`
        # The link should be `media/filename/image.png`. Pandoc usually does this relative to the output file.
        # But let's verify. Pandoc's `--extract-media` treats the path relative to CWD if not absolute? 
        # In convert_docs it uses absolute path for extract-media.
        # Pandoc will write links relative to the output file if possible, or absolute.
        # Let's adjust links to be relative if they are absolute.
        
        # Actually, let's just make sure the media path used in pandoc command matches what we want.
        # We passed `media_dir` (absolute path). Pandoc might generate absolute paths in MD.
        # Let's check and fix.
        
        # Fix absolute paths to relative
        abs_media_dir_pattern = re.escape(media_dir)
        rel_media_path = f"media/{filename_no_ext}"
        
        # Replace absolute path in content with relative path
        # Note: Pandoc might URL encode spaces in paths.
        
        # Actually, best practice with Pandoc `extract-media` is:
        # If we run pandoc from the directory of the output file, we can use relative paths.
        # Or, we just fix it post-processing.
        
        # Simplest fix: replace the absolute path prefix with the relative path
        content = content.replace(media_dir, rel_media_path)
        # Also handle URL encoded version if necessary, but typically standard replace works for raw path if pandas puts raw path.
        # Pandoc usually puts relative path if it can. 
        # Use regex to be safe suitable for the specific `media_dir` structure
        
        # Let's generally cleanup image paths to be relative `media/filename/...`
        # Find `![](/Users/.../media/filename/...)` and replace with `![](media/filename/...)`
        
        def fix_image_path(match):
            full_path = match.group(1)
            if "media" in full_path:
                # Extract part from "media" onwards
                new_path = full_path[full_path.find("media"):]
                return f"![]({new_path})"
            return match.group(0)
            
        content = re.sub(r'!\[\]\((.*?)\)', fix_image_path, content)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        log(f"文件处理完成: {base_name}")
        return True
    except Exception as e:
        log(f"转换失败 {base_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    if not os.path.exists(DOCS_DIR):
        log(f"Error: DOCS_DIR not found: {DOCS_DIR}")
        return

    files = sorted([f for f in os.listdir(DOCS_DIR) if f.endswith(".docx") and not f.startswith("~$")])
    log(f"找到 {len(files)} 个待处理文件")
    
    success_count = 0
    for f in files:
        if convert_file(os.path.join(DOCS_DIR, f)):
            success_count += 1
            
    log(f"全部任务完成！成功: {success_count} / 总数: {len(files)}")
    log(f"输出目录: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
