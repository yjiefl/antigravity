import os
import re

# 设置路径
PROJECT_ROOT = "/Users/yangjie/code/antigravity/doc转markdown处理工具"
MARKDOWN_DIR = os.path.join(PROJECT_ROOT, "markdown")

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
    # 先移除单独成行的 DOI/ISSN 碎片链接 (如 [1000-0526...](...))
    content = re.sub(r'(?m)^\[[\d\.\-a-zA-Z]+\]\(https?://doi\.org/[^\)]+\)\.?\s*$', '', content)
    
    # 智能处理行内 DOI 链接
    def clean_citation_link(match):
        text = match.group(1)
        url = match.group(2)
        dot = match.group(3)
        space = match.group(4)
        
        # 检查是否为冗余信息 (文本包含在URL中)
        if text in url:
            # 特殊保护：如果是年份 (4位数字)，保留
            if text.isdigit() and len(text) == 4 and 1900 <= int(text) <= 2030:
                pass # Flatten, keep text+dot+space
            
            # 如果文本只包含 代码字符 (字母数字点划线斜杠) 且包含数字
            # 认为是 DOI 碎片，删除
            elif re.match(r'^[a-zA-Z0-9\.\-/_]+$', text) and any(c.isdigit() for c in text):
                return "" # Delete everything including dot and space
                
        # 默认行为：扁平化
        return text + dot + space

    content = re.sub(r'\[([^\]]+)\]\((https?://doi\.org/[^\)]+)\)(\.?)(\s*)', clean_citation_link, content)
    
    return content

def process_all_files():
    files = [f for f in os.listdir(MARKDOWN_DIR) if f.endswith(".md") and f != "图表描述汇总.md"]
    for f in files:
        file_path = os.path.join(MARKDOWN_DIR, f)
        print(f"正在深度清洗并排版: {f}")
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            
        cleaned_content = clean_markdown_content(content)
        
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(cleaned_content)
            
    print("排版优化完成。")

if __name__ == "__main__":
    process_all_files()
