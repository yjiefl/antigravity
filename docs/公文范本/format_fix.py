
import re

file_path = '/Users/yangjie/Desktop/code/antigravity/docs/公文范本/公文范本_cleaned.md'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_toc = True
first_h1_found = False

# Patterns to remove
junk_patterns = [
    r'^\d{4}/\d{1,2}/\d{1,2}.*?$', # Date
    r'^\d+-\d+-\d+-\d+.*\.indd \d+$', # Indd
    r'^主\s*编\s+.*$',
    r'^副\s*主\s*编\s+.*$',
    r'^编委会成员\s+.*$',
    r'^.*?王明智.*$', # Names line
    r'^.*?李荣春.*$', # Names line
    r'^编\s*者$',
    r'^2023\s*年\s*5\s*月$'
]

for i, line in enumerate(lines):
    # Check if we reached the first real H1 (Section 1)
    # The first real content section usually starts with "# 一、"
    if re.match(r'^#\s*[一二三四五六七八九十]+\s*、', line):
        first_h1_found = True
        in_toc = False
    
    # Process Junk at the beginning (before first H1)
    if not first_h1_found:
        is_junk = False
        for p in junk_patterns:
            if re.match(p, line.strip()):
                is_junk = True
                break
        if is_junk:
            continue
            
    # Process TOC items (converted to headers by mistake)
    # They look like "## numberText" or "## Text" before the first H1
    if not first_h1_found and line.strip().startswith('## '):
        # Convert "## 1Text" to "1. Text" if possible, or "* 1Text"
        # The previous regex made "## 1..." from "1....".
        # Let's try to restore "1. "
        content = line.strip()[3:] # Remove "## "
        # Check if it starts with a number
        match = re.match(r'^(\d+)(.*)', content)
        if match:
            # Reformat as "1. Text"
            num = match.group(1)
            text = match.group(2)
            new_lines.append(f'{num}. {text}\n')
        else:
            # Just a list item
            new_lines.append(f'* {content}\n')
        continue

    # Clean up empty headers that might be left
    if line.strip() == '##':
        continue
        
    new_lines.append(line)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
