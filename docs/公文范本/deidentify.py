import re
import os

file_path = '/Users/yangjie/Desktop/code/antigravity/docs/公文范本/公文范本_cleaned.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def regex_replace(text, pattern_str, replacement):
    def make_flexible(s):
        return r'\s*'.join(list(s))
    pattern = make_flexible(pattern_str)
    return re.sub(pattern, replacement, text)

# 1. Broad variations of common names and locations
flexible_targets = [
    ('中国南方电网有限责任公司', '[公司名称]'),
    ('南方电网有限责任公司', '[公司名称]'),
    ('南方电网公司', '[公司名称]'),
    ('南方电网', '[公司名称]'),
    ('广西电网', '[省公司]'),
    ('云南电网', '[省公司]'),
    ('广东电网', '[省公司]'),
    ('贵州电网', '[省公司]'),
    ('海南电网', '[省公司]'),
    ('深圳供电局', '[供电局]'),
    ('广州供电局', '[供电局]'),
    ('南方投资集团', '[投资集团]'),
    ('东兰', '[地区]'),
    ('维西', '[地区]'),
    ('河池', '[地区]'),
    ('曲靖', '[地区]'),
    ('宣威', '[地区]'),
    ('英德', '[地区]'),
    ('迪庆', '[地区]'),
    ('怒江', '[地区]'),
    ('深圳', '[地区/城市]'),
    ('广州', '[地区/城市]'),
    ('广东', '[地区/省份]'),
    ('广西', '[地区/省份]'),
    ('云南', '[地区/省份]'),
    ('贵州', '[地区/省份]'),
    ('海南', '[地区/省份]'),
]

for target, replacement in flexible_targets:
    content = regex_replace(content, target, replacement)

# 2. Entity patterns (Fixed to avoid verbs like 站在)
entity_patterns = [
    (r'[\u4e00-\u9fa5]{2,10}(?:供电局|供电分局|供电所|分公司|子公司|发电有限公司|能源发展有限公司|资本控股有限公司|监理公司|数研院|监管局)', '[单位/机构]'),
    (r'[\u4e00-\u9fa5]{2,10}(?:工程|输变电工程|直流工程|交流送出工程|重点项目|项目建设|项目)', '[项目/工程]'),
    (r'[\u4e00-\u9fa5]{2,10}(?:换流站|变电站|电厂|水电站|风电场|抽水蓄能电站)', '[设施/站点]'),
    (r'[\u4e00-\u9fa5]{2,}线(?![条路性段路])', '[具体线路]'),
    (r'[\u4e00-\u9fa5]{2,}站(?![立在他位])', '[具体站点]'),
]

for pattern, replacement in entity_patterns:
    content = re.sub(pattern, replacement, content)

# 3. Specific leftover terms
content = content.replace('南方五[地区/省份]区', '[公司]经营区域五省区')
content = content.replace('连樟村', '[具体村落]')
content = content.replace('新洲大楼', '[办公地点]')
content = content.replace('水贝基地', '[办公地点]')
content = content.replace('粤港澳大湾区', '[大湾区]')

# 4. Clean up "South" abbreviations
content = re.sub(r'南\s*网', '[公司]', content)

# 5. Clean up 文号 (Doc IDs)
content = re.sub(r'[A-Za-z\u4e00-\u9fa5]+〔\d{4}〕\s*\d+号', '[文号]', content)
content = content.replace('广供电办安', '[文号编码]')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Final Comprehensive De-identification complete.")
