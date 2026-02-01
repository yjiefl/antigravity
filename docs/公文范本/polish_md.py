
import re

file_path = '/Users/yangjie/Desktop/code/antigravity/docs/公文范本/公文范本_cleaned.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Split merged main headers
# Pattern: # [一..]、[Category][Content]
# Categories: 决定, 意见, 通知, 通报, 报告, 请示, 批复, 函, 纪要
cats = ['决定', '意见', '通知', '通报', '报告', '请示', '批复', '函', '纪要', '目 录']
for cat in cats:
    cat_clean = cat.replace(' ', '')
    # Handle spaces in category name in regex
    # e.g. "纪要" or "纪 要". The header might be "# 九、纪要公司..."
    # We want to insert newline after the Category.
    
    # Regex for "# Num、CategoryContent"
    # We assume the user's content doesn't start with the category name unless it's the title.
    # But here the problem is "# 九、纪要公司..."
    # We want "# 九、纪要\n\n公司..."
    
    # Match: # [一..]、[Category] [NotNewline]
    p = re.compile(rf'^(#\s*[一二三四五六七八九十]+\s*、\s*{cat_clean})\s*([^\n]+)$', re.MULTILINE)
    content = p.sub(r'\1\n\n\2', content)

# 2. Fix sub-header formatting (restore punctuation)
# ## OneText -> ## One、Text
# ## 1Text -> ## 1. Text
content = re.sub(r'^(##\s*[一二三四五六七八九十]+)(?=[^、\s\n])', r'\1、', content, flags=re.MULTILINE)
content = re.sub(r'^(##\s*\d+)(?=[^.\s\n])', r'\1. ', content, flags=re.MULTILINE)

# 3. Clean up the TOC items that became Headers in List
# My previous script made them lists.
# * 1. Title
# * One、Title
# Just ensure spacing.
content = re.sub(r'^(\*\s*\d+)(?=[^.\s])', r'\1. ', content, flags=re.MULTILINE)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
