import os
import subprocess
import re
from datetime import datetime

# 设置路径
PROJECT_ROOT = "/Users/yangjie/code/antigravity/广西崇左及贵港地区风光资源研究"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "markdown")
LOG_FILE = os.path.join(PROJECT_ROOT, "log/debug.log")
DESC_SUMMARY_FILE = os.path.join(PROJECT_ROOT, "markdown/图表描述汇总.md")

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] DEBUG: {message}\n")
    print(f"[{timestamp}] {message}")

def refine_content(text):
    """
    后处理内容：
    1. 转换 Unicode 下标/上标。
    2. 修复中文加粗间的额外空格。
    3. 转换常用单位和公式为 LaTeX。
    """
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

    # 修复中文加粗间的额外空格 (例如 **摘** **要** -> **摘要**)
    for _ in range(5):
        text = re.sub(r'\*\*\s*([\u4e00-\u9fa5]+)\s*\*\*\s*\*\*\s*([\u4e00-\u9fa5]+)\s*\*\*', r'**\1\2**', text)
    
    # 清理加粗内的空格
    text = re.sub(r'\*\*\s+([^\*]+?)\s+\*\*', r'**\1**', text)
    
    # 修复加粗内有空格的情况，如 **表 1**
    # text = re.sub(r'\*\*\s*([图表])\s*(\d+)\s*\*\*', r'**\1 \2**', text)
    
    # 转换常用单位
    text = text.replace("W/m^{2}", "$W/m^2$")
    text = text.replace("MJ/m^{2}", "$MJ/m^2$")
    text = text.replace("kWh/m^{2}", "$kWh/m^2$")
    text = text.replace("m/s", "$m/s$")
    
    return text

def extract_descriptions(text):
    """
    提取图表描述。
    """
    # 先剥离加粗标签，使匹配更容易
    clean_text = text.replace("**", "")
    
    # 更加宽松的正则：
    # 包含可能的引用号 >
    # 允许图/表 后面有空格或没有
    # 允许编号后面有空格或没有
    pattern = r'(?:^|\n)>?\s*(图|表)\s*(\d+[\.\- ]?\d*)\s*(.*)'
    matches = re.findall(pattern, clean_text)
    
    results = []
    for m in matches:
        label = m[0]
        num = m[1].strip()
        desc = m[2].strip()
        if desc:
            results.append(f"{label} {num} {desc}")
            
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
            
    with open(DESC_SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write("# 图表描述汇总\n\n本文件汇总了所有转换文档中的图表标题描述。\n\n")
        f.write("\n\n".join(all_descs))
        
    log(f"汇总文件已重新生成: {DESC_SUMMARY_FILE}")

if __name__ == "__main__":
    main()
