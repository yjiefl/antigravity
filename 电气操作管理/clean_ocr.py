import os
import re

def clean_ocr_md(file_path):
    if not os.path.exists(file_path):
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    cleaned_lines = []
    # 匹配连字符、点号等垃圾行
    junk_pattern = re.compile(r'^[\s\.\•\-\_…·\r\n]+$')
    # 匹配单独的数字（可能是页码）
    page_num_pattern = re.compile(r'^\s*\d+\s*$')
    # 匹配 TOC 的点号
    toc_dots_pattern = re.compile(r'\.{3,}')

    for line in lines:
        stripped = line.strip()
        # 跳过纯垃圾符号行
        if junk_pattern.match(stripped):
            continue
        # 跳过疑似页码
        if page_num_pattern.match(stripped):
            continue
        
        # 清理行内多余点号
        line = toc_dots_pattern.sub('... ', line)
        
        # 移除一些 OCR 常见的错位字符
        line = line.replace('Iα', 'ICS').replace('DISCONNECTOR', 'disconnector')
        
        cleaned_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(cleaned_lines)

def main():
    target_dir = "/Users/yangjie/code/antigravity/电气操作管理/电气操作"
    files = [
        "GB 26860-2011_电力安全工作规程_发电厂和变电站电气部分(OCR).md",
        "GB26859-2011电力安全工作规程_电力线路部分.md"
    ]
    
    for f in files:
        path = os.path.join(target_dir, f)
        print(f"Cleaning: {f}")
        clean_ocr_md(path)

if __name__ == "__main__":
    main()
