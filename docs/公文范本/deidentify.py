import re
import os

file_path = '/Users/yangjie/Desktop/code/antigravity/docs/公文范本/公文范本_cleaned.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Define replacements (Longer to Shorter)
replacements = [
    # Full Names
    ('中国南方电网有限责任公司', '[公司名称]'),
    ('南方电网资本控股有限公司', '[资本公司]'),
    ('广东电网能源发展有限公司', '[能源发展公司]'),
    ('曲靖宣威风力发电有限公司', '[风力发电公司]'),
    ('输电运行检修分公司', '[检修分公司]'),
    ('超高压输电公司', '[超高压公司]'),
    
    # Provincial Full
    ('贵州电网有限责任公司', '[省公司]'),
    ('云南电网有限责任公司', '[省公司]'),
    ('广东电网有限责任公司', '[省公司]'),
    ('海南电网有限责任公司', '[省公司]'),
    ('广西电网有限责任公司', '[省公司]'),
    
    # Company Short Names
    ('南方电网公司', '[公司名称]'),
    ('中共南方电网公司', '中共[公司名称]'),
    ('贵州电网公司', '[省公司]'),
    ('云南电网公司', '[省公司]'),
    ('广西电网公司', '[省公司]'),
    ('广东电网公司', '[省公司]'),
    ('海南电网公司', '[省公司]'),
    ('调峰调频公司', '[调峰调频公司]'),
    ('超高压公司', '[超高压公司]'),
    ('深圳供电局', '[供电局]'),
    ('广州供电局', '[供电局]'),
    ('后勤管理中心', '[后勤中心]'),
    ('南网数研院', '[数研院]'), 
    
    # Brand Names (Catch-all for remaining "xx Grid")
    ('南方电网', '[公司名称]'),
    ('贵州电网', '[省公司]'),
    ('云南电网', '[省公司]'),
    ('广西电网', '[省公司]'),
    ('广东电网', '[省公司]'),
    ('海南电网', '[省公司]'),
    
    # Common Abbreviations
    ('南网', '[公司]'),
]

# Apply substitutions
# We handle them sequentially.
# If we have "云南电网公司", and we replace "云南电网", we might get "[省公司]公司".
# So the order `云南电网公司` -> `[省公司]` matches first.
# Then `云南电网` -> `[省公司]` matches remaining.

for target, replacement in replacements:
    content = content.replace(target, replacement)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("De-identification complete.")
