import os
import re

# 设置路径
PROJECT_ROOT = "/Users/yangjie/code/antigravity/广西崇左及贵港地区风光资源研究"
MARKDOWN_DIR = os.path.join(PROJECT_ROOT, "markdown")

def clean_markdown_content(content):
    # 1. 移除 bookmark 锚点
    content = re.sub(r'\[\]\{#bookmark\d+ \.anchor\}', '', content)
    
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
        r'中国风能太阳能资源年景公报', r'CHINA WIND AND SOLAR ENERGY RESOURCES BULLETIN',
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

    # 6. 统一单位转换
    content = content.replace(" kwh/m$^{2}$", " $kWh/m^2$")
    content = content.replace(" kWh/m$^{2}$", " $kWh/m^2$")
    content = content.replace(" W/m$^{2}$", " $W/m^2$")
    content = content.replace(" m/s", " $m/s$")
    
    # 7. 移除多余的空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
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
