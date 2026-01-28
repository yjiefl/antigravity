#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill来源管理器
管理skill下载源的增删改查
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import uuid


class SourceManager:
    """Skill来源管理器"""
    
    def __init__(self, config_file: str = None):
        """
        初始化来源管理器
        
        Args:
            config_file: 配置文件路径,默认为skill_manager目录下的sources.json
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            self.config_file = Path(__file__).parent / 'sources.json'
        
        self.sources = self.load_sources()
    
    def load_sources(self) -> List[Dict]:
        """
        加载来源配置
        
        Returns:
            来源列表
        """
        if not self.config_file.exists():
            # 创建默认配置
            default_sources = self._create_default_sources()
            self.save_sources(default_sources)
            return default_sources
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('sources', [])
        except Exception as e:
            print(f"加载来源配置失败: {e}")
            return self._create_default_sources()
    
    def save_sources(self, sources: List[Dict] = None):
        """
        保存来源配置
        
        Args:
            sources: 来源列表,如果为None则保存当前self.sources
        """
        if sources is None:
            sources = self.sources
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'sources': sources}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存来源配置失败: {e}")
    
    def _create_default_sources(self) -> List[Dict]:
        """
        创建默认来源配置
        
        Returns:
            默认来源列表
        """
        return [
            {
                'id': 'anthropic-official',
                'name': 'Anthropic官方Skills',
                'url': 'https://github.com/anthropics/skills',
                'description': 'Anthropic官方skill仓库(包含16个官方skills)',
                'type': 'builtin',
                'skills': [
                    {
                        'name': 'anthropic-skills',
                        'url': 'https://github.com/anthropics/skills.git',
                        'description': '官方完整skill包'
                    }
                ]
            },
            {
                'id': 'composio-awesome',
                'name': 'ComposioHQ Awesome Skills',
                'url': 'https://github.com/ComposioHQ/awesome-claude-skills',
                'description': 'ComposioHQ精选的Claude skills集合',
                'type': 'custom',
                'skills': [
                    {
                        'name': 'awesome-claude-skills',
                        'url': 'https://github.com/ComposioHQ/awesome-claude-skills.git',
                        'description': '包含28个实用skills'
                    }
                ]
            }
        ]
    
    def add_source(self, source_data: Dict) -> tuple[bool, str]:
        """
        添加新来源
        
        Args:
            source_data: 来源数据,包含name, url, description, skills等字段
        
        Returns:
            (成功标志, 消息)
        """
        try:
            # 生成唯一ID
            source_id = str(uuid.uuid4())[:8]
            
            # 构建来源对象
            new_source = {
                'id': source_id,
                'name': source_data.get('name', ''),
                'url': source_data.get('url', ''),
                'description': source_data.get('description', ''),
                'type': 'custom',
                'skills': source_data.get('skills', [])
            }
            
            # 验证必填字段
            if not new_source['name'] or not new_source['url']:
                return False, "名称和URL不能为空"
            
            # 添加到列表
            self.sources.append(new_source)
            self.save_sources()
            
            return True, f"来源 '{new_source['name']}' 添加成功"
        
        except Exception as e:
            return False, f"添加失败: {str(e)}"
    
    def update_source(self, source_id: str, source_data: Dict) -> tuple[bool, str]:
        """
        更新来源
        
        Args:
            source_id: 来源ID
            source_data: 新的来源数据
        
        Returns:
            (成功标志, 消息)
        """
        try:
            # 查找来源
            source = self.get_source(source_id)
            if not source:
                return False, "来源不存在"
            
            # 检查是否是内置来源
            if source.get('type') == 'builtin':
                return False, "内置来源不允许修改"
            
            # 更新数据
            for i, s in enumerate(self.sources):
                if s['id'] == source_id:
                    self.sources[i].update({
                        'name': source_data.get('name', s['name']),
                        'url': source_data.get('url', s['url']),
                        'description': source_data.get('description', s['description']),
                        'skills': source_data.get('skills', s['skills'])
                    })
                    break
            
            self.save_sources()
            return True, "来源更新成功"
        
        except Exception as e:
            return False, f"更新失败: {str(e)}"
    
    def delete_source(self, source_id: str) -> tuple[bool, str]:
        """
        删除来源
        
        Args:
            source_id: 来源ID
        
        Returns:
            (成功标志, 消息)
        """
        try:
            # 查找来源
            source = self.get_source(source_id)
            if not source:
                return False, "来源不存在"
            
            # 检查是否是内置来源
            if source.get('type') == 'builtin':
                return False, "内置来源不允许删除"
            
            # 删除
            self.sources = [s for s in self.sources if s['id'] != source_id]
            self.save_sources()
            
            return True, f"来源 '{source['name']}' 删除成功"
        
        except Exception as e:
            return False, f"删除失败: {str(e)}"
    
    def get_source(self, source_id: str) -> Optional[Dict]:
        """
        获取来源详情
        
        Args:
            source_id: 来源ID
        
        Returns:
            来源对象,如果不存在则返回None
        """
        for source in self.sources:
            if source['id'] == source_id:
                return source
        return None
    
    def list_sources(self) -> List[Dict]:
        """
        列出所有来源
        
        Returns:
            来源列表
        """
        return self.sources
    
    def reload(self):
        """重新加载配置"""
        self.sources = self.load_sources()
