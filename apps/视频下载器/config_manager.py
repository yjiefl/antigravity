#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责保存和加载用户配置
"""

import json
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_dir = Path.home() / '.video_downloader'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load()
    
    def get_defaults(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'download_path': str(Path.home() / 'Downloads' / 'video'),
            'quality': '最佳质量 (best)',
            'browser': 'chrome',
            'download_type': 'video',
            'max_concurrent': 3,  # 最大并发下载数
            'window_geometry': '1000x850',  # 窗口大小
        }
    
    def load(self) -> Dict[str, Any]:
        """加载配置"""
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果配置文件存在,加载它
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 合并默认配置(处理新增的配置项)
                    defaults = self.get_defaults()
                    defaults.update(config)
                    return defaults
            except Exception as e:
                print(f"加载配置失败: {e}, 使用默认配置")
                return self.get_defaults()
        else:
            return self.get_defaults()
    
    def save(self) -> bool:
        """保存配置"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置配置项"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]) -> None:
        """批量更新配置"""
        self.config.update(updates)
