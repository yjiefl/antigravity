import os
import re

# 设置路径
PROJECT_ROOT = "/Users/yangjie/code/antigravity/广西崇左及贵港地区风光资源研究"
MARKDOWN_DIR = os.path.join(PROJECT_ROOT, "markdown")

def final_polish(content):
    # 移除行尾的冗余符号（如误导的 > 或多余空格）
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        l = line.rstrip()
        # 移除行尾的 > 或 >** 这种误识别
        l = re.sub(r'[>\s]+$', '', l)
        cleaned_lines.append(l)
    content = '\n'.join(cleaned_lines)
    
    # 修复加粗结束后紧跟文字没有空格的情况 (可选，但通常 MD 渲染不需要)
    # 修复中文标题间误连的 >
    content = content.replace("**>", "** ")
    
    return content

def process():
    files = [f for f in os.listdir(MARKDOWN_DIR) if f.endswith(".md") and f != "图表描述汇总.md"]
    for f in files:
        file_path = os.path.join(MARKDOWN_DIR, f)
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            
        polished = final_polish(content)
        
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(polished)

if __name__ == "__main__":
    process()
