import os
import subprocess
import time
from datetime import datetime
import re

# 导入现有模块
import convert_docs as converter
import clean_markdown as cleaner
import final_polish as polisher

PROJECT_ROOT = "/Users/yangjie/code/antigravity/doc转markdown处理工具"
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
MARKDOWN_DIR = os.path.join(PROJECT_ROOT, "markdown")
LOG_DIR = os.path.join(PROJECT_ROOT, "log")
DEBUG_LOG = os.path.join(LOG_DIR, "debug.log")

def log_report(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(DEBUG_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] REPORT: {message}\n")
    print(f"[{timestamp}] {message}")

def verify_conversion(filename_no_ext):
    """
    基础核对：检查生成文件是否存在，大小是否合理。
    """
    md_file = os.path.join(MARKDOWN_DIR, f"{filename_no_ext}.md")
    if not os.path.exists(md_file):
        return False, "Markdown 文件未生成"
    
    size = os.path.getsize(md_file)
    if size < 100:
        return False, f"文件过小 ({size} bytes)，可能转换失败"
    
    return True, f"验证通过 (大小: {size} bytes)"

def main():
    start_time = time.time()
    log_report("开始全流程转换任务...")

    # 1. 环境检查
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 获取待处理文件列表
    docx_files = [f for f in os.listdir(DOCS_DIR) if f.endswith(".docx") and not f.startswith("~$")]
    if not docx_files:
        log_report("错误：docs 目录中未找到 .docx 文件")
        return

    log_report(f"共找到 {len(docx_files)} 个待处理文件")

    # 2. 执行转换 (调用 convert_docs.main)
    log_report("步骤 1/3: 执行基础转换与定制逻辑...")
    converter.main()

    # 3. 执行深度清洗 (调用 clean_markdown.process_all_files)
    log_report("步骤 2/3: 执行深度清洗与段落优化...")
    cleaner.process_all_files()

    # 4. 执行最后润色 (调用 final_polish.process)
    log_report("步骤 3/3: 执行最终排版润色...")
    polisher.process()

    # 5. 核对与报告生成
    log_report("-" * 30)
    log_report("转换结果核对报告：")
    success_count = 0
    for f in docx_files:
        name = os.path.splitext(f)[0]
        ok, msg = verify_conversion(name)
        status = "✅ 成功" if ok else "❌ 失败"
        log_report(f"  - {f}: {status} | {msg}")
        if ok: success_count += 1

    duration = time.time() - start_time
    log_report("-" * 30)
    log_report(f"全部任务完成！耗时: {duration:.2f}s")
    log_report(f"成功: {success_count} / 总数: {len(docx_files)}")
    log_report(f"输出目录: {MARKDOWN_DIR}")

if __name__ == "__main__":
    main()
