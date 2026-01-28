#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
下载历史管理模块
记录已下载的视频,避免重复下载
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class HistoryManager:
    """下载历史管理器"""
    
    def __init__(self):
        """初始化历史管理器"""
        self.config_dir = Path.home() / '.video_downloader'
        self.history_file = self.config_dir / 'history.json'
        self.history = self.load()
    
    def load(self) -> Dict[str, Dict]:
        """加载历史记录"""
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果历史文件存在,加载它
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                return {}
        else:
            return {}
    
    def save(self) -> bool:
        """保存历史记录"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存历史记录失败: {e}")
            return False
    
    def add(self, url: str, title: str = "", file_path: str = "") -> None:
        """添加下载记录"""
        self.history[url] = {
            'title': title,
            'file_path': file_path,
            'download_time': datetime.now().isoformat(),
        }
        self.save()
    
    def exists(self, url: str) -> bool:
        """检查URL是否已下载"""
        return url in self.history
    
    def get(self, url: str) -> Optional[Dict]:
        """获取下载记录"""
        return self.history.get(url)
    
    def get_all(self) -> Dict[str, Dict]:
        """获取所有历史记录"""
        return self.history
    
    def remove(self, url: str) -> bool:
        """删除历史记录"""
        if url in self.history:
            del self.history[url]
            self.save()
            return True
        return False
    
    def clear(self) -> None:
        """清空历史记录"""
        self.history = {}
        self.save()
    
    def get_recent(self, limit: int = 10) -> List[Dict]:
        """获取最近的下载记录"""
        items = []
        for url, info in self.history.items():
            items.append({
                'url': url,
                **info
            })
        
        # 按下载时间排序
        items.sort(key=lambda x: x.get('download_time', ''), reverse=True)
        return items[:limit]
