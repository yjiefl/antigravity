import unittest
from source_manager import SourceManager
from pathlib import Path
import json

class TestSourceManager(unittest.TestCase):
    def setUp(self):
        self.manager = SourceManager()

    def test_anthropic_url(self):
        """验证 Anthropic 官方仓库 URL 是否正确"""
        sources = self.manager.list_sources()
        anthropic_source = next((s for s in sources if s['id'] == 'anthropic-official'), None)
        self.assertIsNotNone(anthropic_source)
        self.assertEqual(anthropic_source['url'], 'https://github.com/anthropics/skills')
        
        # 检查内部 skill 的 URL
        skills = anthropic_source.get('skills', [])
        anthropic_skill = next((s for s in skills if s['name'] == 'anthropic-skills'), None)
        self.assertIsNotNone(anthropic_skill)
        self.assertEqual(anthropic_skill['url'], 'https://github.com/anthropics/skills.git')

if __name__ == '__main__':
    unittest.main()
