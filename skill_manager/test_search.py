import unittest

class SearchLogicTest(unittest.TestCase):
    def setUp(self):
        # Sample data matching the structure in SkillManagerGUI.all_skills
        self.all_skills = [
            {
                'name': 'pdf',
                'description': 'PDF toolkit for extracting text and tables',
                'description_zh': 'PDF综合操作工具包',
                'version': '1.0.0',
                'display_source': 'Official'
            },
            {
                'name': 'xlsx',
                'description': 'Spreadsheet creation and analysis tool',
                'description_zh': '综合电子表格创建、编辑和分析工具',
                'version': '1.0.0',
                'display_source': 'Official'
            },
            {
                'name': 'skill-creator',
                'description': 'Guide for creating effective skills',
                'description_zh': 'Skill创建指南',
                'version': '1.0.0',
                'display_source': 'Official'
            }
        ]

    def test_search_name(self):
        query = "pdf"
        results = [s for s in self.all_skills if query.lower() in s['name'].lower()]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'pdf')

    def test_search_description_en(self):
        query = "spreadsheet"
        # Combine matching logic
        results = [s for s in self.all_skills if 
                   query.lower() in s['name'].lower() or 
                   query.lower() in s.get('description', '').lower() or 
                   query.lower() in s.get('description_zh', '').lower()]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'xlsx')

    def test_search_description_zh(self):
        query = "电子表格"
        results = [s for s in self.all_skills if 
                   query.lower() in s['name'].lower() or 
                   query.lower() in s.get('description', '').lower() or 
                   query.lower() in s.get('description_zh', '').lower()]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], 'xlsx')

    def test_search_case_insensitive(self):
        query = "PDF"
        results = [s for s in self.all_skills if query.lower() in s['name'].lower()]
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        query = "nonexistent"
        results = [s for s in self.all_skills if 
                   query.lower() in s['name'].lower() or 
                   query.lower() in s.get('description', '').lower() or 
                   query.lower() in s.get('description_zh', '').lower()]
        self.assertEqual(len(results), 0)

    def test_duplicate_check(self):
        # Add a duplicate skill
        self.all_skills.append({
            'name': 'pdf',
            'description': 'Another PDF tool',
            'path': '/other/path'
        })
        
        from collections import defaultdict
        name_counts = defaultdict(list)
        for skill in self.all_skills:
            name_counts[skill['name']].append(skill)
            
        duplicates = {name: skills for name, skills in name_counts.items() if len(skills) > 1}
        self.assertIn('pdf', duplicates)
        self.assertEqual(len(duplicates['pdf']), 2)

if __name__ == '__main__':
    unittest.main()
