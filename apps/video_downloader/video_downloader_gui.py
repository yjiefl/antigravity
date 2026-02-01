#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube视频下载器 - 图形界面版本
支持视频质量选择、音频下载、批量下载、并发下载和历史记录功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
import yt_dlp
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json

# 导入配置和历史管理器
from config_manager import ConfigManager
from history_manager import HistoryManager


# 下载状态常量
class DownloadStatus:
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"


class YouTubeDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("视频下载器 - YouTube & Bilibili")
        
        # 初始化配置和历史管理器
        self.config_manager = ConfigManager()
        self.history_manager = HistoryManager()
        
        # 从配置加载窗口大小
        geometry = self.config_manager.get('window_geometry', '1000x900')
        self.root.geometry(geometry)
        self.root.resizable(True, True)
        
        # 设置样式
        self.setup_styles()
        
        # 下载队列和状态管理
        self.download_items = {}  # {url: {'status': status, 'title': title, 'index': index}}
        self.is_downloading = False
        self.executor = None
        self.futures = []
        
        # 下载任务选项卡管理
        self.download_tabs = {}  # {url: {'tab': frame, 'progress_bar': bar, 'log_text': text, 'progress_var': var}}
        
        # 从配置加载设置
        self.download_path = self.config_manager.get('download_path')
        os.makedirs(self.download_path, exist_ok=True)
        
        # 创建界面
        self.create_widgets()
        
        # 加载保存的队列
        self.load_queue()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义颜色
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('Info.TLabel', font=('Arial', 10), foreground='#7f8c8d')
        style.configure('TButton', font=('Arial', 10), padding=6)
        style.configure('Action.TButton', font=('Arial', 11, 'bold'))
        
    def create_widgets(self):
        """创建所有界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🎬 视频下载器 (YouTube & Bilibili)", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # URL输入区域
        self.create_url_section(main_frame, row=1)
        
        # 下载选项区域
        self.create_options_section(main_frame, row=2)
        
        # 保存路径区域
        self.create_path_section(main_frame, row=3)
        
        # 批量下载列表
        self.create_batch_section(main_frame, row=4)
        
        # 操作按钮
        self.create_action_buttons(main_frame, row=5)
        
        # 进度显示区域
        self.create_progress_section(main_frame, row=6)
        
        # 日志显示区域
        self.create_log_section(main_frame, row=7)
        
    def create_url_section(self, parent, row):
        """创建URL输入区域"""
        url_frame = ttk.LabelFrame(parent, text="视频URL", padding="10")
        url_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        url_frame.columnconfigure(0, weight=1)
        
        self.url_entry = ttk.Entry(url_frame, font=('Arial', 10))
        self.url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        self.url_entry.insert(0, "请输入YouTube或Bilibili视频URL...")
        self.url_entry.bind('<FocusIn>', self.on_url_focus_in)
        self.url_entry.bind('<FocusOut>', self.on_url_focus_out)
        
        add_btn = ttk.Button(url_frame, text="添加到列表", command=self.add_to_batch)
        add_btn.grid(row=0, column=1)
        
    def create_options_section(self, parent, row):
        """创建下载选项区域"""
        options_frame = ttk.LabelFrame(parent, text="下载选项", padding="10")
        options_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # 下载类型
        ttk.Label(options_frame, text="下载类型:", style='Header.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.download_type = tk.StringVar(value=self.config_manager.get('download_type', 'video'))
        type_frame = ttk.Frame(options_frame)
        type_frame.grid(row=0, column=1, sticky=tk.W)
        
        ttk.Radiobutton(type_frame, text="视频+音频", variable=self.download_type, 
                       value="video").pack(side=tk.LEFT, padx=(0, 15))
        ttk.Radiobutton(type_frame, text="仅音频(MP3)", variable=self.download_type, 
                       value="audio").pack(side=tk.LEFT)
        
        # 视频质量
        ttk.Label(options_frame, text="视频质量:", style='Header.TLabel').grid(
            row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.quality_var = tk.StringVar(value=self.config_manager.get('quality', '最佳质量 (best)'))
        quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var, 
                                     state='readonly', width=30)
        quality_combo['values'] = (
            '最佳质量 (best)',
            '2160p (4K)',
            '1440p (2K)',
            '1080p',
            '720p',
            '480p',
            '360p',
            '最小文件 (worst)'
        )
        quality_combo.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))
        
        # 浏览器选择（用于cookies）
        ttk.Label(options_frame, text="使用浏览器:", style='Header.TLabel').grid(
            row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.browser_var = tk.StringVar(value=self.config_manager.get('browser', 'chrome'))
        browser_combo = ttk.Combobox(options_frame, textvariable=self.browser_var, 
                                     state='readonly', width=30)
        browser_combo['values'] = (
            'chrome',
            'firefox',
            'safari',
            'edge',
            'brave',
            'chromium',
            '不使用cookies'
        )
        browser_combo.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))
        
        # 并发下载数
        ttk.Label(options_frame, text="并发下载数:", style='Header.TLabel').grid(
            row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        
        self.concurrent_var = tk.IntVar(value=self.config_manager.get('max_concurrent', 3))
        concurrent_frame = ttk.Frame(options_frame)
        concurrent_frame.grid(row=3, column=1, sticky=tk.W, pady=(10, 0))
        
        concurrent_spin = ttk.Spinbox(concurrent_frame, from_=1, to=5, 
                                     textvariable=self.concurrent_var, width=10)
        concurrent_spin.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(concurrent_frame, text="(1-5个)", style='Info.TLabel').pack(side=tk.LEFT)
        
    def create_path_section(self, parent, row):
        """创建保存路径区域"""
        path_frame = ttk.LabelFrame(parent, text="保存路径", padding="10")
        path_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(0, weight=1)
        
        self.path_var = tk.StringVar(value=self.download_path)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, 
                              font=('Arial', 10), state='readonly')
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(path_frame, text="浏览...", command=self.browse_path)
        browse_btn.grid(row=0, column=1, padx=(0, 5))
        
        open_folder_btn = ttk.Button(path_frame, text="打开文件夹", command=self.open_download_folder)
        open_folder_btn.grid(row=0, column=2, padx=(0, 5))
        
        history_btn = ttk.Button(path_frame, text="查看历史", command=self.show_history)
        history_btn.grid(row=0, column=3)
        
    def create_batch_section(self, parent, row):
        """创建批量下载列表区域"""
        batch_frame = ttk.LabelFrame(parent, text="下载列表", padding="10")
        batch_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        batch_frame.columnconfigure(0, weight=1)
        batch_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # 创建列表框和滚动条
        list_frame = ttk.Frame(batch_frame)
        list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.batch_listbox = tk.Listbox(list_frame, height=6, font=('Arial', 9),
                                        yscrollcommand=scrollbar.set)
        self.batch_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.batch_listbox.yview)
        
        # 列表操作按钮
        btn_frame = ttk.Frame(batch_frame)
        btn_frame.grid(row=1, column=0, pady=(10, 0))
        
        ttk.Button(btn_frame, text="移除选中", command=self.remove_from_batch).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="清空列表", command=self.clear_batch).pack(side=tk.LEFT)
        
    def create_action_buttons(self, parent, row):
        """创建操作按钮"""
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=row, column=0, pady=(0, 10))
        
        self.download_btn = ttk.Button(btn_frame, text="开始下载", 
                                       style='Action.TButton',
                                       command=self.start_download)
        self.download_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(btn_frame, text="停止下载", 
                                   style='Action.TButton',
                                   command=self.stop_download, state='disabled')
        self.stop_btn.pack(side=tk.LEFT)
        
    def create_progress_section(self, parent, row):
        """创建进度显示区域"""
        progress_frame = ttk.LabelFrame(parent, text="下载进度", padding="10")
        progress_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="等待开始...")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var,
                                  style='Info.TLabel')
        progress_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
    def create_log_section(self, parent, row):
        """创建日志显示区域 - 使用选项卡布局"""
        log_frame = ttk.LabelFrame(parent, text="下载进度", padding="10")
        log_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=2)
        
        # 创建选项卡控件
        self.log_notebook = ttk.Notebook(log_frame)
        self.log_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 创建总览选项卡
        overview_frame = ttk.Frame(self.log_notebook)
        self.log_notebook.add(overview_frame, text="📊 总览")
        
        overview_frame.columnconfigure(0, weight=1)
        overview_frame.rowconfigure(0, weight=1)
        
        self.overview_log = scrolledtext.ScrolledText(overview_frame, height=12, 
                                                      font=('Consolas', 9),
                                                      wrap=tk.WORD, state='disabled')
        self.overview_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 配置日志文本标签用于颜色显示
        self.overview_log.tag_config('pending', foreground='#95a5a6')
        self.overview_log.tag_config('downloading', foreground='#3498db')
        self.overview_log.tag_config('completed', foreground='#27ae60')
        self.overview_log.tag_config('failed', foreground='#e74c3c')
        self.overview_log.tag_config('info', foreground='#34495e')
        
    def on_url_focus_in(self, event):
        """URL输入框获得焦点时清空提示文字"""
        if self.url_entry.get() == "请输入YouTube或Bilibili视频URL...":
            self.url_entry.delete(0, tk.END)
            
    def on_url_focus_out(self, event):
        """URL输入框失去焦点时恢复提示文字"""
        if not self.url_entry.get():
            self.url_entry.insert(0, "请输入YouTube或Bilibili视频URL...")
            
    def browse_path(self):
        """浏览并选择保存路径"""
        path = filedialog.askdirectory(initialdir=self.download_path)
        if path:
            self.download_path = path
            self.path_var.set(path)
            self.config_manager.set('download_path', path)
            self.config_manager.save()
    
    def open_download_folder(self):
        """打开下载文件夹"""
        import subprocess
        import platform
        
        try:
            if platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', self.download_path])
            elif platform.system() == 'Windows':
                subprocess.run(['explorer', self.download_path])
            else:  # Linux
                subprocess.run(['xdg-open', self.download_path])
            self.log_message(f"📂 已打开文件夹: {self.download_path}")
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {str(e)}")
    
    def show_history(self):
        """显示下载历史"""
        history_window = tk.Toplevel(self.root)
        history_window.title("下载历史")
        history_window.geometry("800x500")
        
        # 创建框架
        frame = ttk.Frame(history_window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        history_window.columnconfigure(0, weight=1)
        history_window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # 创建树形视图
        columns = ('title', 'time', 'path')
        tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        tree.heading('title', text='标题')
        tree.heading('time', text='下载时间')
        tree.heading('path', text='文件路径')
        
        tree.column('title', width=300)
        tree.column('time', width=150)
        tree.column('path', width=300)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 加载历史记录
        history = self.history_manager.get_recent(100)
        for item in history:
            title = item.get('title', 'Unknown')
            time = item.get('download_time', '')
            if time:
                try:
                    dt = datetime.fromisoformat(time)
                    time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            path = item.get('file_path', '')
            tree.insert('', tk.END, values=(title, time, path))
        
        # 按钮框架
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(btn_frame, text="清空历史", 
                  command=lambda: self.clear_history(tree)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="关闭", 
                  command=history_window.destroy).pack(side=tk.LEFT)
    
    def clear_history(self, tree):
        """清空历史记录"""
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗?"):
            self.history_manager.clear()
            tree.delete(*tree.get_children())
            self.log_message("✓ 已清空历史记录")
            
    def add_to_batch(self):
        """添加URL到批量下载列表"""
        url = self.url_entry.get().strip()
        if url and url != "请输入YouTube或Bilibili视频URL...":
            # 检查是否已在列表中
            if url in self.download_items:
                messagebox.showwarning("重复", "该URL已在列表中")
                return
            
            # 检查是否已下载过
            if self.history_manager.exists(url):
                history_info = self.history_manager.get(url)
                result = messagebox.askyesnocancel(
                    "已下载过",
                    f"该视频已下载过:\n\n标题: {history_info.get('title', 'Unknown')}\n"
                    f"时间: {history_info.get('download_time', '')}\n\n"
                    f"是否仍要添加到下载列表?"
                )
                if not result:
                    return
            
            # 添加到列表
            index = self.batch_listbox.size()
            display_text = f"⏳ {url}"
            self.batch_listbox.insert(tk.END, display_text)
            self.download_items[url] = {
                'status': DownloadStatus.PENDING,
                'title': '',
                'index': index
            }
            
            self.log_message(f"✓ 已添加到列表: {url}")
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, "请输入YouTube或Bilibili视频URL...")
            
            # 保存队列
            self.save_queue()
        else:
            messagebox.showwarning("提示", "请输入有效的URL")
            
    def remove_from_batch(self):
        """从批量下载列表中移除选中项"""
        selection = self.batch_listbox.curselection()
        if selection:
            index = selection[0]
            # 找到对应的URL
            url_to_remove = None
            for url, info in self.download_items.items():
                if info['index'] == index:
                    url_to_remove = url
                    break
            
            if url_to_remove:
                self.batch_listbox.delete(index)
                del self.download_items[url_to_remove]
                
                # 更新后续项的索引
                for url, info in self.download_items.items():
                    if info['index'] > index:
                        info['index'] -= 1
                
                self.log_message("✓ 已移除选中项")
                self.save_queue()
            
    def clear_batch(self):
        """清空批量下载列表"""
        if self.batch_listbox.size() > 0:
            if messagebox.askyesno("确认", "确定要清空所有下载项吗?"):
                self.batch_listbox.delete(0, tk.END)
                self.download_items.clear()
                self.log_message("✓ 已清空下载列表")
                self.save_queue()
                
    def update_item_status(self, url, status, title=''):
        """更新列表项状态"""
        if url not in self.download_items:
            return
        
        info = self.download_items[url]
        info['status'] = status
        if title:
            info['title'] = title
        
        index = info['index']
        
        # 状态图标
        status_icons = {
            DownloadStatus.PENDING: '⏳',
            DownloadStatus.DOWNLOADING: '⬇️',
            DownloadStatus.COMPLETED: '✅',
            DownloadStatus.FAILED: '❌'
        }
        
        icon = status_icons.get(status, '⏳')
        display_title = title if title else url
        display_text = f"{icon} {display_title}"
        
        # 更新列表项
        self.batch_listbox.delete(index)
        self.batch_listbox.insert(index, display_text)
        
        # 设置颜色
        # 注意: Listbox不直接支持单项颜色,这里我们在日志中用颜色区分
    
    def create_download_tab(self, url, title=''):
        """为下载任务创建独立的选项卡"""
        if url in self.download_tabs:
            return
        
        # 创建选项卡框架
        tab_frame = ttk.Frame(self.log_notebook)
        
        # 截断标题用于选项卡显示
        display_title = title[:20] + '...' if len(title) > 20 else title
        if not display_title:
            display_title = url[:20] + '...'
        
        self.log_notebook.add(tab_frame, text=f"⬇️ {display_title}")
        
        # 配置框架
        tab_frame.columnconfigure(0, weight=1)
        tab_frame.rowconfigure(1, weight=1)
        
        # 创建进度显示区域
        progress_frame = ttk.Frame(tab_frame)
        progress_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度文本
        progress_var = tk.StringVar(value="准备下载...")
        progress_label = ttk.Label(progress_frame, textvariable=progress_var,
                                   font=('Arial', 9))
        progress_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 3))
        
        # 进度条
        progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 创建日志显示区域
        log_text = scrolledtext.ScrolledText(tab_frame, height=10, 
                                            font=('Consolas', 9),
                                            wrap=tk.WORD, state='disabled')
        log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # 配置日志颜色标签
        log_text.tag_config('info', foreground='#34495e')
        log_text.tag_config('success', foreground='#27ae60')
        log_text.tag_config('error', foreground='#e74c3c')
        log_text.tag_config('warning', foreground='#f39c12')
        
        # 保存选项卡信息
        self.download_tabs[url] = {
            'tab': tab_frame,
            'progress_bar': progress_bar,
            'progress_var': progress_var,
            'log_text': log_text
        }
        
        # 切换到新创建的选项卡
        self.log_notebook.select(tab_frame)
    
    def remove_download_tab(self, url):
        """移除下载任务的选项卡"""
        if url not in self.download_tabs:
            return
        
        tab_info = self.download_tabs[url]
        tab_frame = tab_info['tab']
        
        # 从notebook中移除选项卡
        self.log_notebook.forget(tab_frame)
        
        # 从字典中删除
        del self.download_tabs[url]
        
        # 切换回总览选项卡
        if self.log_notebook.index('end') > 0:
            self.log_notebook.select(0)
    
    def update_download_progress(self, url, percent, speed='', eta=''):
        """更新下载任务的进度"""
        if url not in self.download_tabs:
            return
        
        tab_info = self.download_tabs[url]
        
        # 更新进度条
        try:
            percent_num = float(percent.replace('%', ''))
            tab_info['progress_bar']['value'] = percent_num
        except:
            pass
        
        # 更新进度文本
        if speed and eta:
            tab_info['progress_var'].set(f"进度: {percent} | 速度: {speed} | 剩余: {eta}")
        else:
            tab_info['progress_var'].set(f"进度: {percent}")
        
    def log_message(self, message, tag=None, url=None):
        """在日志区域显示消息"""
        # 如果指定了URL,在对应的选项卡中显示
        if url and url in self.download_tabs:
            log_text = self.download_tabs[url]['log_text']
            log_text.config(state='normal')
            if tag:
                log_text.insert(tk.END, message + "\n", tag)
            else:
                log_text.insert(tk.END, message + "\n")
            log_text.see(tk.END)
            log_text.config(state='disabled')
        
        # 同时在总览中显示
        self.overview_log.config(state='normal')
        if tag:
            self.overview_log.insert(tk.END, message + "\n", tag)
        else:
            self.overview_log.insert(tk.END, message + "\n")
        self.overview_log.see(tk.END)
        self.overview_log.config(state='disabled')
        
    def detect_platform(self, url):
        """检测视频平台"""
        if 'bilibili.com' in url or 'b23.tv' in url:
            return 'bilibili'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        else:
            return 'unknown'
        
    def progress_hook(self, d, url):
        """下载进度回调函数"""
        if d['status'] == 'downloading':
            try:
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                
                # 更新主进度条
                percent_num = float(percent.replace('%', ''))
                self.progress_bar['value'] = percent_num
                
                # 更新主进度文本
                title = self.download_items.get(url, {}).get('title', 'Unknown')
                self.progress_var.set(f"下载中: {title[:30]}... | {percent} | 速度: {speed}")
                
                # 更新选项卡进度
                self.root.after(0, lambda: self.update_download_progress(url, percent, speed, eta))
            except:
                pass
                
        elif d['status'] == 'finished':
            self.progress_var.set("正在处理文件...")
            self.progress_bar['value'] = 100
            # 更新选项卡
            if url in self.download_tabs:
                self.download_tabs[url]['progress_var'].set("正在合并文件...")
                self.download_tabs[url]['progress_bar']['value'] = 100
            
    def download_video(self, url):
        """下载单个视频"""
        try:
            # 创建下载任务选项卡
            self.root.after(0, lambda: self.create_download_tab(url))
            
            # 更新状态为下载中
            self.root.after(0, lambda: self.update_item_status(url, DownloadStatus.DOWNLOADING))
            
            # 检测平台
            platform = self.detect_platform(url)
            self.log_message(f"🔍 检测到平台: {platform.upper()}", 'info', url)
            
            # 配置下载选项
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [lambda d: self.progress_hook(d, url)],
                'quiet': False,
                'no_warnings': False,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'no_color': True,
                'extract_flat': False,
                'merge_output_format': 'mp4',
                'fragment_retries': 10,
                'retries': 10,
                'file_access_retries': 3,
                'skip_unavailable_fragments': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Sec-Fetch-Mode': 'navigate',
                },
            }
            
            # 根据平台添加特定配置
            if platform == 'youtube':
                browser = self.browser_var.get()
                if browser != '不使用cookies':
                    try:
                        ydl_opts['cookiesfrombrowser'] = (browser,)
                        self.log_message(f"🔑 使用 {browser} 浏览器的cookies")
                    except Exception as e:
                        self.log_message(f"⚠️  无法读取{browser}浏览器cookies: {str(e)}")
            elif platform == 'bilibili':
                self.log_message("📺 Bilibili视频，使用专用配置")
                ydl_opts['http_headers']['Referer'] = 'https://www.bilibili.com/'
                
                browser = self.browser_var.get()
                if browser != '不使用cookies':
                    try:
                        ydl_opts['cookiesfrombrowser'] = (browser,)
                        self.log_message(f"🔑 使用 {browser} 浏览器的cookies（大会员认证）")
                    except Exception as e:
                        self.log_message(f"⚠️  无法读取cookies: {str(e)}")
            
            # 根据下载类型设置选项
            if self.download_type.get() == 'audio':
                ydl_opts.update({
                    'format': 'bestaudio/best',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
                self.log_message(f"📥 开始下载音频: {url}")
            else:
                quality = self.quality_var.get()
                
                if quality == '最佳质量 (best)':
                    format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
                elif quality == '2160p (4K)':
                    format_str = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]/best'
                elif quality == '1440p (2K)':
                    format_str = 'bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[height<=1440]/best'
                elif quality == '1080p':
                    format_str = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best'
                elif quality == '720p':
                    format_str = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]/best'
                elif quality == '480p':
                    format_str = 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]/best'
                elif quality == '360p':
                    format_str = 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]/best'
                else:
                    format_str = 'worstvideo[ext=mp4]+worstaudio[ext=m4a]/worst'
                
                ydl_opts['format'] = format_str
                self.log_message(f"📥 开始下载视频 ({quality}): {url}")
                
            # 执行下载
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.log_message("🔍 正在获取视频信息...", 'info', url)
                info = ydl.extract_info(url, download=False)
                
                if info:
                    title = info.get('title', 'Unknown')
                    duration = info.get('duration', 0)
                    uploader = info.get('uploader', 'Unknown')
                    
                    # 更新标题和选项卡
                    self.root.after(0, lambda t=title: self.update_item_status(url, DownloadStatus.DOWNLOADING, t))
                    # 更新选项卡标题
                    if url in self.download_tabs:
                        tab_frame = self.download_tabs[url]['tab']
                        display_title = title[:20] + '...' if len(title) > 20 else title
                        tab_index = self.log_notebook.index(tab_frame)
                        self.log_notebook.tab(tab_index, text=f"⬇️ {display_title}")
                    
                    self.log_message(f"📺 标题: {title}", 'info', url)
                    self.log_message(f"👤 作者: {uploader}", 'info', url)
                    if duration:
                        duration = int(duration)
                        mins = duration // 60
                        secs = duration % 60
                        self.log_message(f"⏱️  时长: {mins}:{secs:02d}", 'info', url)
                    
                    # 开始实际下载
                    self.log_message("⬇️  开始下载...", 'info', url)
                    ydl.download([url])
                    
                    # 获取下载的文件路径
                    file_path = ydl.prepare_filename(info)
                    
                    self.log_message(f"✅ 下载完成: {title}", 'success', url)
                    
                    # 更新状态为完成
                    self.root.after(0, lambda t=title: self.update_item_status(url, DownloadStatus.COMPLETED, t))
                    
                    # 添加到历史记录
                    self.history_manager.add(url, title, file_path)
                    
                    # 从列表中移除
                    def remove_completed():
                        if url in self.download_items:
                            index = self.download_items[url]['index']
                            self.batch_listbox.delete(index)
                            del self.download_items[url]
                            
                            # 更新后续项的索引
                            for u, info in self.download_items.items():
                                if info['index'] > index:
                                    info['index'] -= 1
                        
                        # 移除选项卡
                        self.remove_download_tab(url)
                    
                    self.root.after(1000, remove_completed)  # 延迟1秒后移除,让用户看到完成状态
                    
                    return True
                else:
                    self.log_message("❌ 无法获取视频信息", 'error', url)
                    self.root.after(0, lambda: self.update_item_status(url, DownloadStatus.FAILED))
                    self.root.after(2000, lambda: self.remove_download_tab(url))  # 失败后2秒移除选项卡
                    return False
                    
        except Exception as e:
            error_msg = str(e)
            self.log_message(f"❌ 下载失败: {error_msg}", 'error', url)
            self.root.after(0, lambda: self.update_item_status(url, DownloadStatus.FAILED))
            
            # 提供错误提示
            if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
                self.log_message("💡 提示: 请确保选择了正确的浏览器，并且已在该浏览器中登录", 'warning', url)
            elif "empty" in error_msg.lower():
                self.log_message("💡 提示: 文件为空可能是因为视频有地区限制或需要会员", 'warning', url)
            
            self.root.after(2000, lambda: self.remove_download_tab(url))  # 失败后2秒移除选项卡
            return False
            
    def download_worker(self):
        """下载工作线程 - 支持并发下载"""
        urls = [url for url, info in self.download_items.items() 
                if info['status'] == DownloadStatus.PENDING]
        total = len(urls)
        
        if total == 0:
            self.log_message("⚠️  下载列表为空")
            self.is_downloading = False
            self.download_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
            return
            
        self.log_message(f"🚀 开始批量下载，共 {total} 个项目")
        
        max_workers = self.concurrent_var.get()
        self.log_message(f"⚙️  并发下载数: {max_workers}")
        
        success_count = 0
        
        # 使用线程池进行并发下载
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []
        
        try:
            # 提交所有下载任务
            for url in urls:
                if not self.is_downloading:
                    break
                future = self.executor.submit(self.download_video, url)
                self.futures.append((url, future))
            
            # 等待所有任务完成
            for url, future in self.futures:
                if not self.is_downloading:
                    break
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                except Exception as e:
                    self.log_message(f"❌ 任务异常: {str(e)}", 'failed')
        
        finally:
            # 关闭线程池
            self.executor.shutdown(wait=False)
            self.executor = None
            self.futures = []
        
        # 下载完成
        self.is_downloading = False
        self.progress_bar['value'] = 0
        self.progress_var.set(f"下载完成! 成功: {success_count}/{total}")
        self.log_message(f"\n🎉 全部完成! 成功下载 {success_count}/{total} 个文件")
        self.log_message(f"📁 保存位置: {self.download_path}")
        
        # 恢复按钮状态
        self.download_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        
        # 保存队列
        self.save_queue()
        
        # 只在有失败项时才弹出提示对话框
        if success_count < total:
            failed_count = total - success_count
            def show_failure_dialog():
                messagebox.showwarning("下载完成(有失败)", 
                                      f"成功: {success_count} 个\n失败: {failed_count} 个\n\n失败的项目已保留在列表中,可以重试\n保存位置: {self.download_path}")
            
            self.root.after(0, show_failure_dialog)
        
    def start_download(self):
        """开始下载"""
        if self.batch_listbox.size() == 0:
            messagebox.showwarning("提示", "请先添加要下载的视频URL")
            return
            
        if self.is_downloading:
            messagebox.showwarning("提示", "已有下载任务在进行中")
            return
        
        # 保存当前配置
        self.save_config()
        
        # 更新按钮状态
        self.download_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        
        # 清空日志和选项卡
        # 清空总览日志
        self.overview_log.config(state='normal')
        self.overview_log.delete(1.0, tk.END)
        self.overview_log.config(state='disabled')
        
        # 清空所有下载任务选项卡
        for url in list(self.download_tabs.keys()):
            self.remove_download_tab(url)
        
        # 开始下载
        self.is_downloading = True
        download_thread = threading.Thread(target=self.download_worker, daemon=True)
        download_thread.start()
        
    def stop_download(self):
        """停止下载"""
        if messagebox.askyesno("确认", "确定要停止当前下载吗?"):
            self.is_downloading = False
            
            # 取消所有未完成的任务
            if self.executor:
                self.executor.shutdown(wait=False)
            
            self.log_message("\n⏹️  正在停止下载...")
            self.progress_var.set("已停止")
            self.download_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def save_config(self):
        """保存配置"""
        self.config_manager.update({
            'download_path': self.download_path,
            'quality': self.quality_var.get(),
            'browser': self.browser_var.get(),
            'download_type': self.download_type.get(),
            'max_concurrent': self.concurrent_var.get(),
            'window_geometry': self.root.geometry(),
        })
        self.config_manager.save()
    
    def save_queue(self):
        """保存下载队列"""
        queue_file = Path.home() / '.video_downloader' / 'queue.json'
        queue_file.parent.mkdir(parents=True, exist_ok=True)
        
        queue_data = {
            'items': [
                {
                    'url': url,
                    'status': info['status'],
                    'title': info['title']
                }
                for url, info in self.download_items.items()
            ]
        }
        
        try:
            with open(queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存队列失败: {e}")
    
    def load_queue(self):
        """加载下载队列"""
        queue_file = Path.home() / '.video_downloader' / 'queue.json'
        
        if not queue_file.exists():
            return
        
        try:
            with open(queue_file, 'r', encoding='utf-8') as f:
                queue_data = json.load(f)
            
            items = queue_data.get('items', [])
            for item in items:
                url = item['url']
                status = item.get('status', DownloadStatus.PENDING)
                title = item.get('title', '')
                
                # 只加载未完成的项目
                if status != DownloadStatus.COMPLETED:
                    index = self.batch_listbox.size()
                    
                    status_icons = {
                        DownloadStatus.PENDING: '⏳',
                        DownloadStatus.FAILED: '❌'
                    }
                    icon = status_icons.get(status, '⏳')
                    display_text = f"{icon} {title if title else url}"
                    
                    self.batch_listbox.insert(tk.END, display_text)
                    self.download_items[url] = {
                        'status': DownloadStatus.PENDING,  # 重置为待下载
                        'title': title,
                        'index': index
                    }
            
            if items:
                self.log_message(f"✓ 已恢复 {len(items)} 个下载项")
        
        except Exception as e:
            print(f"加载队列失败: {e}")
    
    def on_closing(self):
        """窗口关闭事件"""
        # 保存配置和队列
        self.save_config()
        self.save_queue()
        
        # 如果正在下载,询问是否确认退出
        if self.is_downloading:
            if messagebox.askyesno("确认退出", "下载正在进行中,确定要退出吗?\n\n未完成的下载将在下次启动时恢复。"):
                self.is_downloading = False
                if self.executor:
                    self.executor.shutdown(wait=False)
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """主函数"""
    root = tk.Tk()
    app = YouTubeDownloaderGUI(root)
    
    # 窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()
