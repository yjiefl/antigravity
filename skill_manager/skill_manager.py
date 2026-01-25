#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill管理器 - 核心模块
支持skill的安装、卸载、下载和管理
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import zipfile
import tempfile
from datetime import datetime


class SkillManager:
    """Skill管理器核心类"""
    
    def __init__(self, skills_dir: str = None):
        """
        初始化Skill管理器
        
        Args:
            skills_dir: skills存储目录,默认为当前目录下的skills文件夹
        """
        if skills_dir is None:
            self.skills_dir = Path(__file__).parent / 'skills'
        else:
            self.skills_dir = Path(skills_dir)
        
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.skills_dir / 'skills_config.json'
        self.config = self.load_config()
    
        # 加载预翻译库
        self.translation_library = self.load_translation_library()
    def load_config(self) -> Dict:
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载配置失败: {e}")
                return {'installed_skills': {}, 'repositories': []}
        return {'installed_skills': {}, 'repositories': []}
    
    def save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def list_skills(self) -> List[Dict]:
        """
        列出所有已安装的skills
        支持两种skill包格式:
        1. 包含skills/子文件夹的仓库 (如anthropic-skills)
        2. 根目录包含多个skill子目录的仓库 (如awesome-claude-skills)
        
        Returns:
            skill信息列表
        """
        skills = []
        
        for skill_name, skill_info in self.config['installed_skills'].items():
            skill_path = self.skills_dir / skill_name
            if not skill_path.exists():
                continue
            
            # 方式1: 检查是否有skills/子文件夹
            skills_subdir = skill_path / 'skills'
            if skills_subdir.exists() and skills_subdir.is_dir():
                # 这是一个skill包,扫描skills/目录中的所有skills
                for sub_skill_dir in skills_subdir.iterdir():
                    if sub_skill_dir.is_dir():
                        skill_md = sub_skill_dir / 'SKILL.md'
                        if skill_md.exists():
                            skill_md_info = self.parse_skill_md(skill_md)
                            
                            skills.append({
                                'name': skill_md_info.get('skill_name', sub_skill_dir.name),
                                'path': str(sub_skill_dir),
                                'version': skill_info.get('version', 'unknown'),
                                'description': skill_md_info.get('skill_description', ''),
                                'description_zh': skill_md_info.get('skill_description_zh', ''),
                                'author': skill_info.get('author', ''),
                                'installed_at': skill_info.get('installed_at', ''),
                                'source': skill_info.get('source', ''),
                                'package_name': skill_name,
                                'is_from_package': True
                            })
            else:
                # 方式2: 检查根目录是否包含多个skill子目录
                skill_dirs = []
                for item in skill_path.iterdir():
                    if item.is_dir():
                        skill_md = item / 'SKILL.md'
                        if skill_md.exists():
                            skill_dirs.append(item)
                
                if len(skill_dirs) > 1:
                    # 根目录包含多个skills,作为skill包处理
                    for sub_skill_dir in skill_dirs:
                        skill_md = sub_skill_dir / 'SKILL.md'
                        skill_md_info = self.parse_skill_md(skill_md)
                        
                        skills.append({
                            'name': skill_md_info.get('skill_name', sub_skill_dir.name),
                            'path': str(sub_skill_dir),
                            'version': skill_info.get('version', 'unknown'),
                            'description': skill_md_info.get('skill_description', ''),
                            'description_zh': skill_md_info.get('skill_description_zh', ''),
                            'author': skill_info.get('author', ''),
                            'installed_at': skill_info.get('installed_at', ''),
                            'source': skill_info.get('source', ''),
                            'package_name': skill_name,
                            'is_from_package': True
                        })
                else:
                    # 这是一个独立的skill
                    skills.append({
                        'name': skill_name,
                        'path': str(skill_path),
                        'version': skill_info.get('version', 'unknown'),
                        'description': skill_info.get('description', ''),
                        'author': skill_info.get('author', ''),
                        'installed_at': skill_info.get('installed_at', ''),
                        'source': skill_info.get('source', ''),
                        'is_from_package': False
                    })
        
        return skills
    
    def install_skill(self, skill_path: str, skill_name: str = None, force: bool = False) -> tuple[bool, str]:
        """
        安装skill(从本地路径)
        
        Args:
            skill_path: skill的本地路径
            skill_name: skill名称,如果不指定则使用文件夹名
            force: 是否强制覆盖已存在的skill
        
        Returns:
            (是否成功, 消息)
        """
        source_path = Path(skill_path)
        
        if not source_path.exists():
            return False, f"路径不存在: {skill_path}"
        
        # 确定skill名称
        if skill_name is None:
            skill_name = source_path.name
        
        target_path = self.skills_dir / skill_name
        
        # 检查是否已安装
        if target_path.exists() and not force:
            return False, f"Skill '{skill_name}' 已存在,使用force=True强制覆盖"
        
        try:
            # 删除已存在的
            if target_path.exists():
                shutil.rmtree(target_path)
            
            # 复制skill文件
            if source_path.is_dir():
                shutil.copytree(source_path, target_path)
            else:
                target_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
            
            # 读取skill信息
            skill_info = self.read_skill_info(target_path)
            
            # 更新配置
            self.config['installed_skills'][skill_name] = {
                'version': skill_info.get('version', '1.0.0'),
                'description': skill_info.get('description', ''),
                'author': skill_info.get('author', ''),
                'installed_at': datetime.now().isoformat(),
                'source': str(source_path)
            }
            self.save_config()
            
            return True, f"Skill '{skill_name}' 安装成功!"
            
        except Exception as e:
            if target_path.exists():
                shutil.rmtree(target_path)
            return False, f"安装失败: {str(e)}"
    
    def download_skill(self, url: str, skill_name: str = None, progress_callback=None) -> tuple[bool, str]:
        """
        从URL下载并安装skill
        
        Args:
            url: skill的下载URL (支持.zip文件或git仓库)
            skill_name: skill名称,如果不指定则自动推断
            progress_callback: 进度回调函数 callback(message: str)
        
        Returns:
            (是否成功, 消息)
        """
        def log(msg):
            if progress_callback:
                progress_callback(msg)
            print(msg)
        
        log(f"📥 开始下载: {url}")
        
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # 判断是git仓库还是zip文件
                if url.endswith('.git') or 'github.com' in url or 'gitlab.com' in url:
                    log("🔍 检测到Git仓库")
                    return self.download_from_git(url, skill_name, temp_path, log)
                elif url.endswith('.zip'):
                    log("🔍 检测到ZIP文件")
                    return self.download_from_zip(url, skill_name, temp_path, log)
                else:
                    return False, "不支持的URL格式,请提供.zip文件或Git仓库URL"
                    
        except Exception as e:
            return False, f"下载失败: {str(e)}"
    
    def download_from_git(self, url: str, skill_name: str, temp_path: Path, log_func) -> tuple[bool, str]:
        """从Git仓库下载skill"""
        try:
            # 检查git是否可用
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                return False, "Git未安装,请先安装Git"
            
            # 克隆仓库
            log_func("📦 正在克隆仓库...")
            clone_path = temp_path / 'repo'
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', url, str(clone_path)],
                capture_output=True, text=True
            )
            
            if result.returncode != 0:
                return False, f"克隆失败: {result.stderr}"
            
            # 确定skill名称
            if skill_name is None:
                skill_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            
            log_func("✓ 克隆完成")
            
            # 安装skill
            success, msg = self.install_skill(str(clone_path), skill_name, force=True)
            return success, msg
            
        except Exception as e:
            return False, f"Git下载失败: {str(e)}"
    
    def download_from_zip(self, url: str, skill_name: str, temp_path: Path, log_func) -> tuple[bool, str]:
        """从ZIP文件下载skill"""
        try:
            # 下载ZIP文件
            log_func("📦 正在下载ZIP文件...")
            zip_path = temp_path / 'skill.zip'
            
            urllib.request.urlretrieve(url, zip_path)
            log_func("✓ 下载完成")
            
            # 解压ZIP文件
            log_func("📂 正在解压...")
            extract_path = temp_path / 'extracted'
            extract_path.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # 查找skill目录(可能在子目录中)
            skill_dirs = list(extract_path.iterdir())
            if len(skill_dirs) == 1 and skill_dirs[0].is_dir():
                skill_source = skill_dirs[0]
            else:
                skill_source = extract_path
            
            # 确定skill名称
            if skill_name is None:
                skill_name = skill_source.name
            
            log_func("✓ 解压完成")
            
            # 安装skill
            success, msg = self.install_skill(str(skill_source), skill_name, force=True)
            return success, msg
            
        except Exception as e:
            return False, f"ZIP下载失败: {str(e)}"
    
    def uninstall_skill(self, skill_name: str) -> tuple[bool, str]:
        """
        卸载skill
        
        Args:
            skill_name: skill名称
        
        Returns:
            (是否成功, 消息)
        """
        skill_path = self.skills_dir / skill_name
        
        if not skill_path.exists():
            return False, f"Skill '{skill_name}' 不存在"
        
        try:
            shutil.rmtree(skill_path)
            
            # 更新配置
            if skill_name in self.config['installed_skills']:
                del self.config['installed_skills'][skill_name]
                self.save_config()
            
            return True, f"Skill '{skill_name}' 已卸载"
            
        except Exception as e:
            return False, f"卸载失败: {str(e)}"
    
    def read_skill_info(self, skill_path: Path) -> Dict:
        """
        读取skill信息
        
        Args:
            skill_path: skill路径
        
        Returns:
            skill信息字典
        """
        info = {
            'version': '1.0.0',
            'description': '',
            'author': ''
        }
        
        # 尝试读取package.json或skill.json
        for config_file in ['skill.json', 'package.json', 'config.json']:
            config_path = skill_path / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        info['version'] = data.get('version', info['version'])
                        info['description'] = data.get('description', info['description'])
                        info['author'] = data.get('author', info['author'])
                        break
                except:
                    pass
        
        return info
    
    def get_skill_info(self, skill_name: str, skill_path: str = None) -> Optional[Dict]:
        """
        获取指定skill的详细信息
        
        Args:
            skill_name: skill名称
            skill_path: skill路径(可选,用于skill包中的skills)
        
        Returns:
            skill信息,如果不存在返回None
        """
        # 如果提供了skill_path,直接使用
        if skill_path:
            skill_path_obj = Path(skill_path)
            if not skill_path_obj.exists():
                return None
            
            info = {
                'name': skill_name,
                'path': str(skill_path_obj),
                'version': 'unknown',
                'description': '',
                'author': ''
            }
        else:
            # 原有逻辑:从config中查找
            if skill_name not in self.config['installed_skills']:
                return None
            
            skill_path_obj = self.skills_dir / skill_name
            if not skill_path_obj.exists():
                return None
            
            info = self.config['installed_skills'][skill_name].copy()
            info['name'] = skill_name
            info['path'] = str(skill_path_obj)
        
        # 读取文件列表
        files = []
        for item in skill_path_obj.rglob('*'):
            if item.is_file():
                files.append(str(item.relative_to(skill_path_obj)))
        info['files'] = files
        info['file_count'] = len(files)
        
        # 解析SKILL.md文件
        skill_md_path = skill_path_obj / 'SKILL.md'
        if skill_md_path.exists():
            skill_md_info = self.parse_skill_md(skill_md_path)
            info.update(skill_md_info)
        
        return info
    
    def parse_skill_md(self, skill_md_path: Path) -> Dict:
        """
        解析SKILL.md文件
        
        Args:
            skill_md_path: SKILL.md文件路径
        
        Returns:
            解析出的信息字典
        """
        result = {
            'skill_description': '',
            'skill_description_zh': '',  # 中文描述
            'skill_content': '',
            'has_skill_md': True,
            'skill_name': '',
            'skill_version': '1.0.0'
        }
        
        try:
            with open(skill_md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取YAML frontmatter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1].strip()
                    body = parts[2].strip()
                    
                    # 更健壮的YAML解析
                    current_key = None
                    current_value = []
                    
                    for line in frontmatter.split('\n'):
                        # 检查是否是新的键值对
                        if ':' in line and not line.startswith(' ') and not line.startswith('\t'):
                            # 保存之前的键值对
                            if current_key:
                                value_str = ' '.join(current_value).strip()
                                # 移除引号
                                if value_str.startswith('"') and value_str.endswith('"'):
                                    value_str = value_str[1:-1]
                                
                                if current_key == 'name':
                                    result['skill_name'] = value_str
                                elif current_key == 'description':
                                    result['skill_description'] = value_str
                                    result['skill_description_zh'] = self.translate_to_chinese(value_str, result.get('skill_name'))
                                elif current_key == 'version':
                                    result['skill_version'] = value_str
                            
                            # 开始新的键值对
                            key, value = line.split(':', 1)
                            current_key = key.strip()
                            current_value = [value.strip()]
                        else:
                            # 继续当前值(多行值)
                            if current_key:
                                current_value.append(line.strip())
                    
                    # 保存最后一个键值对
                    if current_key:
                        value_str = ' '.join(current_value).strip()
                        if value_str.startswith('"') and value_str.endswith('"'):
                            value_str = value_str[1:-1]
                        
                        if current_key == 'name':
                            result['skill_name'] = value_str
                        elif current_key == 'description':
                            result['skill_description'] = value_str
                            result['skill_description_zh'] = self.translate_to_chinese(value_str, result.get('skill_name'))
                        elif current_key == 'version':
                            result['skill_version'] = value_str
                    
                    result['skill_content'] = body
                else:
                    result['skill_content'] = content
            else:
                result['skill_content'] = content
                
        except Exception as e:
            result['skill_content'] = f"Error reading SKILL.md: {str(e)}"
            result['has_skill_md'] = False
        
        return result
    
    def translate_to_chinese(self, text: str) -> str:
        """改进的英文到中文翻译"""
        if not text:
            return ""
        
        import re

    
    def load_translation_library(self) -> Dict:
        """加载预翻译库"""
        translation_file = Path(__file__).parent / 'skill_translations.json'
        if translation_file.exists():
            try:
                with open(translation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    def translate_to_chinese(self, text: str, skill_name: str = None) -> str:
        """改进的英文到中文翻译,优先使用预翻译库"""
        if not text:
            return ""
        
        # 优先使用预翻译库
        if skill_name and hasattr(self, 'translation_library'):
            if skill_name in self.translation_library:
                return self.translation_library[skill_name].get('zh', '')
        
        # 如果没有预翻译,使用自动翻译
        import re
        
        translations = {
            'Guide for creating effective skills': 'Skill创建指南',
            'This skill should be used when users want to': '使用场景:用户想要',
            'with support for': '支持', 'at scale': '大规模地',
            'spreadsheet': '电子表格', 'document': '文档',
            'creating': '创建', 'editing': '编辑', 'analyzing': '分析',
            'extracting': '提取', 'merging': '合并', 'splitting': '拆分',
            'manipulation': '操作', 'toolkit': '工具包',
            'comprehensive': '综合', 'Comprehensive': '综合',
            'formulas': '公式', 'formatting': '格式化',
            'interactive': '交互式', 'parameter': '参数',
            'algorithmic art': '算法艺术', 'generative art': '生成艺术',
            'when': '当', 'with': '具有', 'for': '用于',
            'needs to': '需要', 'programmatically': '以编程方式',
        }
        
        result = text
        sorted_translations = sorted(translations.items(), key=lambda x: len(x[0]), reverse=True)
        
        for en, zh in sorted_translations:
            pattern = r'\b' + re.escape(en) + r'\b'
            result = re.sub(pattern, zh, result, flags=re.IGNORECASE)
        
        result = re.sub(r'\s+', ' ', result).strip()
        
        chinese_char_count = len([c for c in result if '\u4e00' <= c <= '\u9fff'])
        if chinese_char_count < len(result) * 0.25:
            return f"[自动翻译] {result}"
        
        return result

