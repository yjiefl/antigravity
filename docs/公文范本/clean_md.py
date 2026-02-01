import re
import os

def clean_markdown(content):
    # 1. Remove image placeholders
    content = re.sub(r'!\[\]\(media/image\d+\.png\)\{.*?\}', '', content)
    content = re.sub(r'!\[\]\(media/image\d+\.png\)', '', content)

    # 2. Remove horizontal artifacts and table junk
    content = re.sub(r'^[-\s+]{10,}$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\|.*\|$', '', content, flags=re.MULTILINE)

    # 3. Remove anchor/bookmark noise
    content = re.sub(r'\[\]\{#bookmark\d+.*?\}', '', content)
    
    # 4. Remove Pandoc-style blockquotes
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        if line.strip().startswith('>'):
            line = re.sub(r'^>\s*', '', line)
        cleaned_lines.append(line)
    content = '\n'.join(cleaned_lines)

    # 5. Remove running headers/footers and redundant titles
    categories = ['决 定', '意 见', '通 知', '通 报', '报 告', '请 示', '批 复', '函', '纪 要', '目 录']
    for cat in categories:
        # Match lines that are just the category name
        content = re.sub(rf'^(?:##\s*)?{cat.replace(" ", "\s*")}\s*$', '', content, flags=re.MULTILINE)
        # Restore valid section headers as # Headers
        content = re.sub(rf'^\s*([一二三四五六七八九十]、\s*{cat.replace(" ", "\s*")})\s*$', r'# \1', content, flags=re.MULTILINE)

    # Remove empty headings left over
    content = re.sub(r'^##\s*$', '', content, flags=re.MULTILINE)

    # 6. Clean up Table of Contents
    # Remove broken bookmark links (convert [Text](#bookmark...) to just Text)
    # Since anchors were removed, these links are dead.
    content = re.sub(r'\[(.*?)\]\(#bookmark.*?\)', r'\1', content)
    
    # 7. Fix typography
    content = re.sub(r'(\d+)\s*．', r'\1.', content)
    content = re.sub(r'（\s*([一二三四五六七八九十0-9/.\-]+)\s*）', r'（\1）', content)
    content = re.sub(r'([一二三四五六七八九十])\s*、', r'\1、', content) # 一 、 -> 一、
    
    # 8. Fix main title and remove publication junk
    # Remove .indd, ISBN, CIP lines which usually appear at the start
    content = re.sub(r'^.*?\.indd\s+\d+.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^.*?ISBN\s+[0-9\-]+.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^.*?CIP.*?数据.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^.*?版\s*权\s*专\s*有.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^.*?本书如有印装质量问题.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^.*?编\s*委\s*会.*$', '', content, flags=re.MULTILINE)
            
    content = re.sub(r'^公文范本\s*$', r'# 公文范本', content, count=1, flags=re.MULTILINE)
    
    # 9. Clean up excessive empty lines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # 10. Join broken lines (experimental)
    # Join a line that doesn't end with punctuation and isn't a header/list
    lines = content.split('\n')
    merged_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i < len(lines) - 1:
            next_line = lines[i+1].strip()
            # If current line is not empty and doesn't end with punctuation
            # and next line is not empty and doesn't look like a header/list/date
            # Enhanced regex to protect likely headers or list items
            if line and not re.search(r'[。！？：；”\s]$', line) and \
               next_line and not re.match(r'^(?:#|\d+\.|（?[一二三四五六七八九十0-9]+）?|[一二三四五六七八九十]、|\d{4}年|附件|主\s*编|副\s*主\s*编)', next_line):
                line = line + next_line
                i += 1 # Skip next line as it's merged
        merged_lines.append(line)
        i += 1
    content = '\n'.join(merged_lines)
    
    # 11. Format sub-headers (Experiment)
    # Identify lines like "1. Text" or "(1) Text" that are not # Headers but look like headers
    # Convert them to ## headers.
    # Ensure it's not already a markdown list item (e.g., "1. " at the start of a line is a list)
    # This regex tries to capture common patterns for sub-headers:
    # - "1. " or "1、"
    # - "(1)" or "（1）"
    # - "一、" or "（一）"
    # It avoids lines that already start with '#' (existing headers)
    content = re.sub(r'^(?!\s*#)(?:\s*(\d+)\.\s*|\s*(\d+)、\s*|\s*\((\d+)\)\s*|\s*（(\d+)）\s*|\s*([一二三四五六七八九十])、\s*|\s*（([一二三四五六七八九十])）\s*)([^\n]+)$', r'## \1\2\3\4\5\6\7', content, flags=re.MULTILINE)

    # 12. Ensure standard empty lines around headers and paragraphs
    # Add an empty line before any line starting with '##' if not already present
    content = re.sub(r'([^\n])\n(##\s)', r'\1\n\n\2', content)
    # Add an empty line after any line starting with '##' if not already present
    content = re.sub(r'(##[^\n]*)\n([^\n])', r'\1\n\n\2', content)
    
    # Final cleanup
    content = re.sub(r'\n{2,}', '\n\n', content)
    
    return content

input_path = '/Users/yangjie/Desktop/code/antigravity/docs/公文范本/公文范本_cleaned.md'
output_path = '/Users/yangjie/Desktop/code/antigravity/docs/公文范本/公文范本_cleaned.md'

with open(input_path, 'r', encoding='utf-8') as f:
    text = f.read()

cleaned_text = clean_markdown(text)

with open(output_path, 'w', encoding='utf-8') as f:
    f.write(cleaned_text)
