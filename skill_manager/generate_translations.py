#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成Skill描述翻译库
扫描所有skills并创建预翻译的中文描述
"""

from pathlib import Path
import json
import sys
sys.path.insert(0, '/Users/yangjie/Desktop/code/antigravity/skill_manager')

from skill_manager import SkillManager

# 手工翻译的高质量中文描述
MANUAL_TRANSLATIONS = {
    # Anthropic官方skills
    'pdf': 'PDF综合操作工具包,用于提取文本和表格、创建新PDF、合并/拆分文档以及处理表单。当Claude需要填写PDF表单或以编程方式大规模处理、生成或分析PDF文档时使用。',
    'xlsx': '综合电子表格创建、编辑和分析工具,支持公式、格式化、数据分析和可视化。当Claude需要处理电子表格(.xlsx, .xlsm, .csv, .tsv等)时使用,包括:(1)创建带公式和格式的新电子表格,(2)读取或分析数据,(3)修改现有电子表格并保留公式,(4)在电子表格中进行数据分析和可视化,或(5)重新计算公式。',
    'pptx': 'PowerPoint演示文稿创建和编辑工具,支持幻灯片设计、内容布局和格式化。用于创建专业的演示文稿。',
    'docx': 'Word文档创建和编辑工具,支持文档格式化、样式和内容管理。用于创建和编辑专业文档。',
    'algorithmic-art': '使用p5.js创建算法艺术,具有种子随机性和交互式参数探索功能。当用户请求使用代码创建艺术、生成艺术、算法艺术、流场或粒子系统时使用。创建原创算法艺术而不是复制现有艺术家的作品以避免版权侵犯。',
    'skill-creator': 'Skill创建指南。当用户想要创建新skill(或更新现有skill)以扩展Claude的能力,提供专业知识、工作流或工具集成时使用。',
    'theme-factory': '主题样式工具包,用于为作品应用主题。这些作品可以是幻灯片、文档、网页等。',
    'doc-coauthoring': '引导用户完成文档协作编写的结构化工作流。当用户想要与Claude协作编写文档时使用。',
    'frontend-design': '前端设计工具,用于创建现代化的网页界面和用户体验设计。',
    'canvas-design': 'Canvas设计工具,用于创建图形和可视化内容。',
    'brand-guidelines': '品牌指南工具,帮助创建和维护一致的品牌形象和设计规范。',
    'internal-comms': '内部沟通工具,用于创建和管理组织内部的沟通内容。',
    'mcp-builder': 'MCP(Model Context Protocol)服务器构建工具,用于创建和配置MCP服务器。',
    'slack-gif-creator': 'Slack GIF创建工具,用于为Slack创建动画GIF表情和内容。',
    'web-artifacts-builder': 'Web作品构建工具,用于创建交互式网页应用和组件。',
    'webapp-testing': 'Web应用测试工具,用于测试和验证Web应用的功能和性能。',
    
    # ComposioHQ awesome-claude-skills
    'content-research-writer': '内容研究写作助手,通过进行研究来协助撰写高质量内容。',
    'tailored-resume-generator': '定制简历生成器,分析职位描述并生成针对性的简历,突出相关技能和经验。',
    'langsmith-fetch': 'LangSmith调试工具,通过获取执行跟踪来调试LangChain和LangGraph代理。',
    'template-skill': 'Skill模板,用于创建新的Claude skills的起始模板。',
    'youtube-downloader': 'YouTube视频下载器,支持自定义质量和格式下载YouTube视频。',
    'raffle-winner-picker': '抽奖工具,从列表、电子表格或Google Sheets中随机选择获奖者。',
    'skill-share': 'Skill分享工具,创建新的Claude skills并自动分享到社区。',
    'developer-growth-analysis': '开发者成长分析工具,分析你最近的Claude Code聊天历史,识别编码模式和成长领域。',
    'domain-name-brainstormer': '域名创意生成器,为你的项目生成创意域名并检查可用性。',
    'image-enhancer': '图像增强工具,提高图像质量,特别是截图,通过增强清晰度和细节。',
    'connect-apps': '应用连接器,将Claude连接到Gmail、Slack、GitHub等外部应用。',
    'invoice-organizer': '发票整理工具,自动整理发票和收据用于税务准备。',
    'twitter-algorithm-optimizer': 'Twitter算法优化器,使用Twitter算法分析和优化推文以获得最大曝光。',
    'changelog-generator': '更新日志生成器,从git提交历史自动创建面向用户的更新日志。',
    'artifacts-builder': '作品构建器,用于创建复杂的多组件claude.ai HTML作品的工具套件。',
    'competitive-ads-extractor': '竞品广告提取器,从广告库(Facebook、Google等)提取和分析竞争对手的广告。',
    'file-organizer': '文件整理工具,智能地在你的计算机上整理文件和文件夹。',
    'connect': '应用连接工具,将Claude连接到任何应用。发送邮件、创建问题、发布消息等。',
    'meeting-insights-analyzer': '会议洞察分析器,分析会议记录和录音,发现行为模式和可操作的洞察。',
    'lead-research-assistant': '潜在客户研究助手,通过分析公司数据和在线信息识别高质量潜在客户。',
}

def generate_translation_library():
    """生成翻译库"""
    manager = SkillManager()
    
    # 获取所有skills
    skills = manager.list_skills()
    
    translation_library = {}
    
    print(f"找到 {len(skills)} 个skills,开始生成翻译库...\n")
    
    for skill in skills:
        skill_name = skill['name']
        description = skill.get('description', '')
        
        if not description:
            continue
        
        # 优先使用手工翻译
        if skill_name in MANUAL_TRANSLATIONS:
            translation_library[skill_name] = {
                'en': description,
                'zh': MANUAL_TRANSLATIONS[skill_name],
                'source': 'manual'
            }
            print(f"✓ {skill_name}: 使用手工翻译")
        else:
            # 使用自动翻译
            zh_translation = manager.translate_to_chinese(description)
            translation_library[skill_name] = {
                'en': description,
                'zh': zh_translation,
                'source': 'auto'
            }
            print(f"○ {skill_name}: 使用自动翻译")
    
    return translation_library

if __name__ == '__main__':
    # 生成翻译库
    library = generate_translation_library()
    
    # 保存到JSON文件
    output_file = '/Users/yangjie/Desktop/code/antigravity/skill_manager/skill_translations.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(library, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 翻译库已保存到: {output_file}")
    print(f"✓ 共翻译 {len(library)} 个skills")
    
    # 统计
    manual_count = sum(1 for v in library.values() if v['source'] == 'manual')
    auto_count = sum(1 for v in library.values() if v['source'] == 'auto')
    print(f"  - 手工翻译: {manual_count} 个")
    print(f"  - 自动翻译: {auto_count} 个")
