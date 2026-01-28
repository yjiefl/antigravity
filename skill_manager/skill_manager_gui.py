#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skill管理器 - GUI界面
提供图形化的skill管理界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from pathlib import Path
from skill_manager import SkillManager
from source_manager import SourceManager


class SkillManagerGUI:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Skill管理器")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # 初始化管理器
        self.manager = SkillManager()
        self.source_manager = SourceManager()
        self.current_lang = "zh"  # 当前显示语言: zh=中文, en=英文
        self.all_skills = []      # 存储所有的 skill 数据以供搜索
        self.search_var = tk.StringVar()  # 搜索框变量
        self.search_var.trace_add("write", self.on_search_change) # 监听搜索框变化
        
        # 设置样式
        self.setup_styles()
        
        # 创建界面
        self.create_widgets()
        
        # 加载skills列表
        self.refresh_skills()
    
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Arial', 11, 'bold'), foreground='#34495e')
        style.configure('TButton', font=('Arial', 10), padding=6)
        style.configure('Action.TButton', font=('Arial', 11, 'bold'))
    
    def create_widgets(self):
        """创建所有界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📦 Skill管理器", style='Title.TLabel')
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 下载区域
        self.create_download_section(main_frame, row=1)
        
        # Skills列表
        self.create_skills_list_section(main_frame, row=2)
        
        # 操作按钮
        self.create_action_buttons(main_frame, row=3)
        
        # 日志显示
        self.create_log_section(main_frame, row=4)
    
    def create_download_section(self, parent, row):
        """创建下载区域"""
        download_frame = ttk.LabelFrame(parent, text="下载Skill", padding="10")
        download_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        download_frame.columnconfigure(0, weight=1)
        
        # URL输入
        url_frame = ttk.Frame(download_frame)
        url_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        url_frame.columnconfigure(0, weight=1)
        
        ttk.Label(url_frame, text="URL:", style='Header.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.url_entry = ttk.Entry(url_frame, font=('Arial', 10))
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        self.url_entry.insert(0, "输入Git仓库URL或ZIP文件URL...")
        self.url_entry.bind('<FocusIn>', self.on_url_focus_in)
        self.url_entry.bind('<FocusOut>', self.on_url_focus_out)
        
        # Skill名称(可选)
        name_frame = ttk.Frame(download_frame)
        name_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        name_frame.columnconfigure(1, weight=1)
        
        ttk.Label(name_frame, text="名称(可选):", style='Header.TLabel').grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        self.name_entry = ttk.Entry(name_frame, font=('Arial', 10))
        self.name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.download_btn = ttk.Button(name_frame, text="下载", 
                                       style='Action.TButton',
                                       command=self.download_skill)
        self.download_btn.grid(row=0, column=2, padx=(0, 5))
        
        # 浏览仓库按钮
        ttk.Button(name_frame, text="📚 浏览仓库", 
                  command=self.browse_repositories).grid(row=0, column=3)
    
    def create_skills_list_section(self, parent, row):
        """创建Skills列表区域"""
        list_frame = ttk.LabelFrame(parent, text="已安装的Skills", padding="10")
        list_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(1, weight=1)
        parent.rowconfigure(row, weight=1)
        
        # 搜索栏
        search_frame = ttk.Frame(list_frame)
        search_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="🔍 搜索:", style='Header.TLabel').grid(row=0, column=0, padx=(0, 5))
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, font=('Arial', 10))
        self.search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # 清空搜索按钮
        ttk.Button(search_frame, text="重置", command=lambda: self.search_var.set(""), width=5).grid(row=0, column=2, padx=(5, 0))

        # 创建Treeview
        columns = ('name', 'version', 'description', 'source')
        self.skills_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=8)
        
        self.skills_tree.heading('name', text='名称')
        self.skills_tree.heading('version', text='版本')
        self.skills_tree.heading('description', text='描述')
        self.skills_tree.heading('source', text='来源')
        
        self.skills_tree.column('name', width=180)
        self.skills_tree.column('version', width=80)
        self.skills_tree.column('description', width=350)
        self.skills_tree.column('source', width=150)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.skills_tree.yview)
        self.skills_tree.configure(yscrollcommand=scrollbar.set)
        
        self.skills_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 添加双击事件
        self.skills_tree.bind('<Double-1>', lambda e: self.show_skill_info())
    
    def create_action_buttons(self, parent, row):
        """创建操作按钮"""
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=row, column=0, pady=(0, 10))
        
        ttk.Button(btn_frame, text="刷新列表", command=self.refresh_skills).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="安装本地Skill", command=self.install_local_skill).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="卸载选中", command=self.uninstall_selected).pack(
            side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="查看详情", command=self.show_skill_info).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="📝 生成翻译", command=self.generate_translations).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="⚙️ 管理来源", command=self.show_source_manager).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🌐 切换语言", command=self.toggle_language).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🔍 查找重复", command=self.check_duplicates).pack(side=tk.LEFT, padx=(0, 5))
    
    def create_log_section(self, parent, row):
        """创建日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(row, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, 
                                                  font=('Consolas', 9),
                                                  wrap=tk.WORD, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置日志颜色
        self.log_text.tag_config('success', foreground='#27ae60')
        self.log_text.tag_config('error', foreground='#e74c3c')
        self.log_text.tag_config('info', foreground='#3498db')
    
    def on_url_focus_in(self, event):
        """URL输入框获得焦点"""
        if self.url_entry.get() == "输入Git仓库URL或ZIP文件URL...":
            self.url_entry.delete(0, tk.END)
    
    def on_url_focus_out(self, event):
        """URL输入框失去焦点"""
        if not self.url_entry.get():
            self.url_entry.insert(0, "输入Git仓库URL或ZIP文件URL...")
    
    def log_message(self, message, tag=None):
        """在日志区域显示消息"""
        self.log_text.config(state='normal')
        if tag:
            self.log_text.insert(tk.END, message + "\n", tag)
        else:
            self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def toggle_language(self):
        """切换描述显示语言"""
        if self.current_lang == "zh":
            self.current_lang = "en"
            self.log_message("🌐 已切换到英文描述", 'info')
        else:
            self.current_lang = "zh"
            self.log_message("🌐 已切换到中文描述", 'info')
        self.refresh_skills()
    
    def refresh_skills(self):
        """刷新skills列表"""
        # 清空列表
        for item in self.skills_tree.get_children():
            self.skills_tree.delete(item)
        
        # 加载skills
        skills = self.manager.list_skills()
        self.all_skills = []
        
        for skill in skills:
            # 确定来源
            source = '未知'
            if skill.get('is_from_package'):
                package_name = skill.get('package_name', '')
                if 'anthropic' in package_name.lower() or 'example-skill' in package_name.lower():
                    source = '官方 (Anthropic)'
                else:
                    source = f'Skill包: {package_name}'
            else:
                skill_source = skill.get('source', '')
                if 'github.com/anthropics' in skill_source:
                    source = '官方 (Anthropic)'
                elif 'github.com' in skill_source:
                    source = 'GitHub'
                elif skill_source:
                    source = '本地安装'
                else:
                    source = '未知'
            
            skill['display_source'] = source
            self.all_skills.append(skill)
            
        # 应用当前过滤器
        self.apply_filter(self.search_var.get().lower())
        
        if not self.search_var.get():
            self.log_message(f"✓ 已加载 {len(skills)} 个skills", 'info')
            
            # 自动检查重复并提示
            dup_names = set()
            seen_names = set()
            for s in self.all_skills:
                if s['name'] in seen_names:
                    dup_names.add(s['name'])
                seen_names.add(s['name'])
            
            if dup_names:
                self.log_message(f"⚠️ 注意: 发现 {len(dup_names)} 个名称重复的 Skill，建议查看！", 'error')

    def on_search_change(self, *args):
        """搜索框内容变化回调"""
        query = self.search_var.get().lower()
        self.apply_filter(query)

    def apply_filter(self, query):
        """根据关键词过滤并显示 skills"""
        # 清空当前列表
        for item in self.skills_tree.get_children():
            self.skills_tree.delete(item)
            
        filtered_count = 0
        for skill in self.all_skills:
            # 搜索匹配: 名称, 英文描述, 中文描述
            name_match = query in skill['name'].lower()
            desc_en_match = query in skill.get('description', '').lower()
            desc_zh_match = query in skill.get('description_zh', '').lower()
            
            if name_match or desc_en_match or desc_zh_match:
                # 根据当前语言选择描述
                if self.current_lang == "zh" and skill.get('description_zh'):
                    desc = skill.get('description_zh', '')
                else:
                    desc = skill.get('description', '')
                
                display_desc = desc[:50] + '...' if len(desc) > 50 else desc if desc else ""
                
                self.skills_tree.insert('', tk.END, values=(
                    skill['name'],
                    skill['version'],
                    display_desc,
                    skill['display_source']
                ))
                filtered_count += 1
        
        # 如果正在搜索，且有结果，记录搜索结果数量
        pass

    def check_duplicates(self):
        """查找并提示重复名称的 skill"""
        from collections import defaultdict
        
        name_counts = defaultdict(list)
        for skill in self.all_skills:
            name_counts[skill['name']].append(skill)
            
        duplicates = {name: skills for name, skills in name_counts.items() if len(skills) > 1}
        
        if not duplicates:
            messagebox.showinfo("重复检查", "未发现重复名称的 Skill。")
            return
            
        # 创建结果窗口
        dup_window = tk.Toplevel(self.root)
        dup_window.title("发现重复 Skill")
        dup_window.geometry("800x500")
        
        frame = ttk.Frame(dup_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dup_window.columnconfigure(0, weight=1)
        dup_window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        ttk.Label(frame, text="以下 Skill 名称存在重复，请检查：", 
                 font=('Arial', 12, 'bold'), foreground='#e74c3c').grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # 使用 Treeview 显示重复详情
        columns = ('name', 'version', 'source', 'path')
        dup_tree = ttk.Treeview(frame, columns=columns, show='headings', height=15)
        
        dup_tree.heading('name', text='名称')
        dup_tree.heading('version', text='版本')
        dup_tree.heading('source', text='来源')
        dup_tree.heading('path', text='完整路径')
        
        dup_tree.column('name', width=120)
        dup_tree.column('version', width=80)
        dup_tree.column('source', width=150)
        dup_tree.column('path', width=400)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=dup_tree.yview)
        dup_tree.configure(yscrollcommand=scrollbar.set)
        
        dup_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 填充数据
        for name, skills in duplicates.items():
            # 为每组重复添加一个空行作为分隔
            for skill in skills:
                dup_tree.insert('', tk.END, values=(
                    skill['name'],
                    skill['version'],
                    skill.get('display_source', '未知'),
                    skill['path']
                ))
            # 插入分隔线感视觉效果
            dup_tree.insert('', tk.END, values=("-"*20, "-"*10, "-"*20, "-"*50))
            
        ttk.Button(frame, text="关闭", command=dup_window.destroy).grid(row=2, column=0, pady=(15, 0))
    
    def download_skill(self):
        """下载skill"""
        url = self.url_entry.get().strip()
        if not url or url == "输入Git仓库URL或ZIP文件URL...":
            messagebox.showwarning("提示", "请输入有效的URL")
            return
        
        skill_name = self.name_entry.get().strip() or None
        
        # 禁用下载按钮
        self.download_btn.config(state='disabled')
        self.log_message(f"📥 开始下载: {url}", 'info')
        
        def download_thread():
            def progress_callback(msg):
                self.root.after(0, lambda: self.log_message(msg, 'info'))
            
            success, msg = self.manager.download_skill(url, skill_name, progress_callback)
            
            def on_complete():
                self.download_btn.config(state='normal')
                if success:
                    self.log_message(msg, 'success')
                    self.refresh_skills()
                    self.url_entry.delete(0, tk.END)
                    self.url_entry.insert(0, "输入Git仓库URL或ZIP文件URL...")
                    self.name_entry.delete(0, tk.END)
                else:
                    self.log_message(msg, 'error')
            
            self.root.after(0, on_complete)
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def install_local_skill(self):
        """安装本地skill"""
        path = filedialog.askdirectory(title="选择Skill文件夹")
        if not path:
            return
        
        skill_name = Path(path).name
        result = messagebox.askyesno("确认", f"安装skill: {skill_name}?")
        if not result:
            return
        
        self.log_message(f"📦 安装本地skill: {path}", 'info')
        success, msg = self.manager.install_skill(path, force=True)
        
        if success:
            self.log_message(msg, 'success')
            self.refresh_skills()
        else:
            self.log_message(msg, 'error')
    
    def generate_translations(self):
        """重新生成翻译库"""
        if not messagebox.askyesno("生成翻译", "确定要重新扫描所有Skill并生成翻译库吗?\n(这将更新中文描述)"):
            return
            
        self.log_message("📝 开始更新翻译库...", 'info')
        
        def run():
            def progress_callback(msg):
                self.root.after(0, lambda: self.log_message(msg, 'info'))
                
            success, msg = self.manager.generate_translations(progress_callback)
            
            def on_complete():
                if success:
                    self.log_message(msg, 'success')
                    messagebox.showinfo("成功", msg)
                    self.refresh_skills()
                else:
                    self.log_message(msg, 'error')
                    messagebox.showerror("失败", msg)
                    
            self.root.after(0, on_complete)
            
        threading.Thread(target=run, daemon=True).start()

    def uninstall_selected(self):
        """卸载选中的skill (支持批量删除)"""
        selection = self.skills_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择要卸载的skill")
            return
        
        skills_to_delete = []
        for sel in selection:
            item = self.skills_tree.item(sel)
            skill_name = item['values'][0]
            
            # 从本地缓存中匹配对应的 skill 数据
            skill_data = None
            for s in self.all_skills:
                if s['name'] == skill_name:
                    skill_data = s
                    break
            
            if skill_data:
                skills_to_delete.append(skill_data)

        if not skills_to_delete:
            return

        # 4. 构建确认消息
        if len(skills_to_delete) == 1:
            skill = skills_to_delete[0]
            if skill.get('is_from_package'):
                msg = f"确定要卸载 '{skill['name']}' 吗?\n(注意: 这只会删除该单个 Skill, 不会删除整个 '{skill['package_name']}' 包)"
            else:
                msg = f"确定要卸载 '{skill['name']}' 吗?"
        else:
            msg = f"确定要卸载选中的 {len(skills_to_delete)} 个 Skill 吗?"

        if not messagebox.askyesno("确认卸载", msg):
            return

        # 5. 执行卸载逻辑
        success_count = 0
        error_msgs = []
        
        for skill in skills_to_delete:
            display_name = skill['name']
            # 如果是包中的 skill, 传递路径参数以实现精细删除
            if skill.get('is_from_package'):
                success, res_msg = self.manager.uninstall_skill(skill['package_name'], skill['path'])
            else:
                success, res_msg = self.manager.uninstall_skill(skill['name'])
            
            if success:
                success_count += 1
                self.log_message(f"🗑️ {res_msg}", 'success')
            else:
                error_msgs.append(f"{display_name}: {res_msg}")
                self.log_message(f"❌ {display_name} 卸载失败: {res_msg}", 'error')

        # 6. 最终反馈
        if success_count > 0:
            self.refresh_skills()
        
        if error_msgs:
            messagebox.showerror("部分卸载失败", f"以下 Skill 卸载失败:\n" + "\n".join(error_msgs))
    
    def show_skill_info(self):
        """显示skill详细信息"""
        selection = self.skills_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请先选择一个skill")
            return
        
        item = self.skills_tree.item(selection[0])
        skill_name = item['values'][0]
        
        # 从缓存中找到对应的 skill
        skill_data = None
        for skill in self.all_skills:
            if skill['name'] == skill_name:
                skill_data = skill
                break
        
        if not skill_data:
            messagebox.showerror("错误", "无法找到skill信息")
            return
        
        # 获取详细信息,传递路径参数
        info = self.manager.get_skill_info(skill_name, skill_data.get('path'))
        if not info:
            messagebox.showerror("错误", "无法获取skill信息")
            return
        
        # 创建信息窗口
        info_window = tk.Toplevel(self.root)
        info_window.title(f"Skill信息 - {skill_name}")
        info_window.geometry("800x600")
        
        frame = ttk.Frame(info_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_window.columnconfigure(0, weight=1)
        info_window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # 创建Notebook用于分页显示
        notebook = ttk.Notebook(frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 基本信息选项卡
        basic_frame = ttk.Frame(notebook, padding="10")
        notebook.add(basic_frame, text="📋 基本信息")
        
        basic_frame.columnconfigure(1, weight=1)
        
        # 显示基本信息
        row = 0
        
        # 确定来源
        source_text = '未知'
        if skill_data.get('is_from_package'):
            package_name = skill_data.get('package_name', '')
            if 'anthropic' in package_name.lower() or 'example-skill' in package_name.lower():
                source_text = '官方 (Anthropic)'
            else:
                source_text = f'Skill包: {package_name}'
        else:
            skill_source = skill_data.get('source', '')
            if 'github.com/anthropics' in skill_source:
                source_text = '官方 (Anthropic)'
            elif 'github.com' in skill_source:
                source_text = f'GitHub: {skill_source}'
            elif skill_source:
                source_text = f'本地: {skill_source}'
        
        # 准备描述数据
        desc_en = info.get('skill_description') or info.get('description', 'No description')
        desc_zh = info.get('skill_description_zh', '')
        current_lang = [desc_zh and 'zh' or 'en']  # 使用列表以便在闭包中修改
        
        for key, value in [
            ('名称', info['name']),
            ('版本', info.get('skill_version', info.get('version', 'unknown'))),
            ('来源', source_text),
            ('作者', info.get('author', 'unknown')),
            ('安装时间', info.get('installed_at', '')),
            ('路径', info['path']),
            ('文件数量', info.get('file_count', 0)),
        ]:
            ttk.Label(basic_frame, text=f"{key}:", font=('Arial', 10, 'bold')).grid(
                row=row, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            
            if key == '来源':
                value_text = tk.Text(basic_frame, height=1, width=60, font=('Arial', 10), 
                                    wrap=tk.WORD, relief=tk.FLAT, borderwidth=0)
                value_text.insert('1.0', str(value))
                value_text.config(state='disabled')
                value_text.grid(row=row, column=1, sticky=tk.W, pady=5)
            else:
                value_label = ttk.Label(basic_frame, text=str(value), font=('Arial', 10))
                value_label.grid(row=row, column=1, sticky=tk.W, pady=5)
            row += 1
        
        # 描述字段(带切换功能)
        ttk.Label(basic_frame, text="描述:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.NW, pady=5, padx=(0, 10))
        
        desc_container = ttk.Frame(basic_frame)
        desc_container.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        desc_text = tk.Text(desc_container, height=4, width=60, font=('Arial', 10), 
                           wrap=tk.WORD, relief=tk.FLAT, borderwidth=0)
        desc_text.pack(side=tk.TOP, anchor=tk.W)
        
        if desc_zh:
            button_frame = ttk.Frame(desc_container)
            button_frame.pack(side=tk.TOP, anchor=tk.W, pady=(5, 0))
            
            toggle_btn = ttk.Button(button_frame, text='🌐 切换到英文')
            
            def toggle_language():
                if current_lang[0] == 'en':
                    current_lang[0] = 'zh'
                    desc_text.config(state='normal')
                    desc_text.delete('1.0', tk.END)
                    desc_text.insert('1.0', desc_zh)
                    desc_text.config(state='disabled')
                    toggle_btn.config(text='🌐 切换到英文')
                else:
                    current_lang[0] = 'en'
                    desc_text.config(state='normal')
                    desc_text.delete('1.0', tk.END)
                    desc_text.insert('1.0', desc_en)
                    desc_text.config(state='disabled')
                    toggle_btn.config(text='🌐 切换到中文')
            
            toggle_btn.config(command=toggle_language)
            toggle_btn.pack(side=tk.LEFT)
            desc_text.insert('1.0', desc_zh)
        else:
            desc_text.insert('1.0', desc_en)
        
        desc_text.config(state='disabled')
        row += 1
        
        # 功能说明选项卡
        if info.get('has_skill_md', False):
            function_frame = ttk.Frame(notebook, padding="10")
            notebook.add(function_frame, text="📖 功能说明")
            
            function_frame.columnconfigure(0, weight=1)
            function_frame.rowconfigure(0, weight=1)
            
            # 显示SKILL.md内容
            skill_text = scrolledtext.ScrolledText(function_frame, height=20, width=70,
                                                   font=('Consolas', 10), wrap=tk.WORD)
            skill_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            
            # 插入内容
            content = info.get('skill_content', 'No content available')
            skill_text.insert(tk.END, content)
            skill_text.config(state='disabled')
        
        # 文件列表选项卡
        files_frame = ttk.Frame(notebook, padding="10")
        notebook.add(files_frame, text="📁 文件列表")
        
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(0, weight=1)
        
        files_text = scrolledtext.ScrolledText(files_frame, height=20, width=70,
                                              font=('Consolas', 9))
        files_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        for file in info.get('files', []):
            files_text.insert(tk.END, file + "\n")
        files_text.config(state='disabled')
    
    def browse_repositories(self):
        """浏览预设skill仓库"""
        # 创建仓库浏览窗口
        repo_window = tk.Toplevel(self.root)
        repo_window.title("浏览Skill仓库")
        repo_window.geometry("800x600")
        
        frame = ttk.Frame(repo_window, padding="20")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        repo_window.columnconfigure(0, weight=1)
        repo_window.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        
        # 标题
        ttk.Label(frame, text="📚 预设Skill仓库", 
                 font=('Arial', 14, 'bold')).grid(row=0, column=0, pady=(0, 15))
        
        # 创建Notebook用于分类显示
        notebook = ttk.Notebook(frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 从 source_manager 获取所有来源
        self.source_manager.reload()
        repositories = self.source_manager.list_sources()
        
        # 如果没有来源，显示提示
        if not repositories:
            ttk.Label(frame, text="暂无配置的来源，请先添加来源", 
                     font=('Arial', 12)).grid(row=1, column=0, pady=20)
            return
        
        # 为每个仓库创建一个选项卡
        for repo in repositories:
            tab_frame = ttk.Frame(notebook, padding="10")
            notebook.add(tab_frame, text=repo['name'])
            
            tab_frame.columnconfigure(0, weight=1)
            tab_frame.rowconfigure(1, weight=1)
            
            # 仓库描述
            desc_frame = ttk.Frame(tab_frame)
            desc_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
            desc_frame.columnconfigure(1, weight=1)
            
            ttk.Label(desc_frame, text="描述:", font=('Arial', 10, 'bold')).grid(
                row=0, column=0, sticky=tk.W, padx=(0, 10))
            ttk.Label(desc_frame, text=repo['description'], 
                     font=('Arial', 10)).grid(row=0, column=1, sticky=tk.W)
            
            ttk.Label(desc_frame, text="仓库:", font=('Arial', 10, 'bold')).grid(
                row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
            
            url_label = ttk.Label(desc_frame, text=repo['url'], 
                                 font=('Arial', 10), foreground='#3498db', cursor='hand2')
            url_label.grid(row=1, column=1, sticky=tk.W, pady=(5, 0))
            
            # 点击URL复制到剪贴板
            url_label.bind('<Button-1>', lambda e, url=repo['url']: self.copy_to_clipboard(url))
            
            # Skills列表
            ttk.Label(tab_frame, text="可用Skills:", 
                     font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky=tk.NW, pady=(10, 5))
            
            # 创建skills列表框架
            skills_frame = ttk.Frame(tab_frame)
            skills_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            skills_frame.columnconfigure(0, weight=1)
            skills_frame.rowconfigure(0, weight=1)
            tab_frame.rowconfigure(2, weight=1)
            
            # 创建Treeview显示skills
            columns = ('name', 'description')
            skills_tree = ttk.Treeview(skills_frame, columns=columns, show='headings', height=10)
            
            skills_tree.heading('name', text='名称')
            skills_tree.heading('description', text='描述')
            
            skills_tree.column('name', width=200)
            skills_tree.column('description', width=400)
            
            # 添加滚动条
            scrollbar = ttk.Scrollbar(skills_frame, orient=tk.VERTICAL, command=skills_tree.yview)
            skills_tree.configure(yscrollcommand=scrollbar.set)
            
            skills_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            
            # 填充skills数据
            for skill in repo['skills']:
                skills_tree.insert('', tk.END, values=(
                    skill['name'],
                    skill['description']
                ))
            
            # 双击下载skill
            def on_double_click(event, tree=skills_tree, repo_skills=repo['skills']):
                selection = tree.selection()
                if selection:
                    item = tree.item(selection[0])
                    skill_name = item['values'][0]
                    # 查找对应的skill URL
                    for skill in repo_skills:
                        if skill['name'] == skill_name:
                            self.url_entry.delete(0, tk.END)
                            self.url_entry.insert(0, skill['url'])
                            self.name_entry.delete(0, tk.END)
                            self.name_entry.insert(0, skill['name'])
                            repo_window.destroy()
                            self.log_message(f"已选择: {skill_name}", 'info')
                            break
            
            skills_tree.bind('<Double-1>', on_double_click)
            
            # 添加下载按钮
            btn_frame = ttk.Frame(tab_frame)
            btn_frame.grid(row=3, column=0, pady=(10, 0))
            
            def download_selected(tree=skills_tree, repo_skills=repo['skills']):
                selection = tree.selection()
                if not selection:
                    messagebox.showwarning("提示", "请先选择一个skill")
                    return
                
                item = tree.item(selection[0])
                skill_name = item['values'][0]
                # 查找对应的skill URL
                for skill in repo_skills:
                    if skill['name'] == skill_name:
                        self.url_entry.delete(0, tk.END)
                        self.url_entry.insert(0, skill['url'])
                        self.name_entry.delete(0, tk.END)
                        self.name_entry.insert(0, skill['name'])
                        repo_window.destroy()
                        # 自动开始下载
                        self.download_skill()
                        break
            
            ttk.Button(btn_frame, text="下载选中的Skill", 
                      command=download_selected).pack(side=tk.LEFT, padx=(0, 5))
            
            ttk.Label(btn_frame, text="(或双击skill直接选择)", 
                     font=('Arial', 9), foreground='#7f8c8d').pack(side=tk.LEFT)
    
    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.log_message(f"✓ 已复制到剪贴板: {text}", 'info')







    def show_add_source_dialog(self, parent, callback=None):
        """显示添加来源对话框"""
        import tkinter.messagebox as messagebox
        
        dialog = tk.Toplevel(parent)
        dialog.title("添加Skill来源")
        dialog.geometry("600x300")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        row = 0
        ttk.Label(main_frame, text="来源名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=50)
        name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(main_frame, text="仓库URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, width=50)
        url_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(例: https://github.com/user/repo)", 
                 font=('Arial', 8), foreground='gray').grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        ttk.Label(main_frame, text="描述:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(main_frame, width=50)
        desc_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Skill名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        skill_name_entry = ttk.Entry(main_frame, width=50)
        skill_name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(可选,留空则使用仓库名)", 
                 font=('Arial', 8), foreground='gray').grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        def save():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            desc = desc_entry.get().strip()
            skill_name = skill_name_entry.get().strip()
            
            if not name or not url:
                messagebox.showerror("错误", "名称和URL不能为空")
                return
            
            # 从URL提取仓库名作为skill名称
            if not skill_name:
                skill_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            
            skills = [{
                'name': skill_name,
                'url': url if url.endswith('.git') else url + '.git',
                'description': desc
            }]
            
            source_data = {
                'name': name,
                'url': url,
                'description': desc,
                'skills': skills
            }
            
            success, message = self.source_manager.add_source(source_data)
            if success:
                messagebox.showinfo("成功", message)
                dialog.destroy()
                if callback:
                    callback()
            else:
                messagebox.showerror("错误", message)
        
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_source_manager(self):
        """显示来源管理窗口"""
        import tkinter.messagebox as messagebox
        
        source_window = tk.Toplevel(self.root)
        source_window.title("Skill来源管理")
        source_window.geometry("700x500")
        
        main_frame = ttk.Frame(source_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        source_window.columnconfigure(0, weight=1)
        source_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        ttk.Label(main_frame, text="Skill下载来源:", font=('Arial', 12, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        columns = ('name', 'url', 'type')
        source_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=12)
        source_tree.heading('name', text='来源名称')
        source_tree.heading('url', text='仓库URL')
        source_tree.heading('type', text='类型')
        source_tree.column('name', width=200)
        source_tree.column('url', width=350)
        source_tree.column('type', width=80)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=source_tree.yview)
        source_tree.configure(yscrollcommand=scrollbar.set)
        source_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        def refresh_sources():
            for item in source_tree.get_children():
                source_tree.delete(item)
            self.source_manager.reload()
            sources = self.source_manager.list_sources()
            for source in sources:
                type_text = '内置' if source.get('type') == 'builtin' else '自定义'
                source_tree.insert('', tk.END, values=(
                    source['name'], source['url'], type_text
                ), tags=(source['id'],))
        
        refresh_sources()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=(10, 0), sticky=tk.W)
        
        def delete_source():
            selection = source_tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请先选择要删除的来源")
                return
            item = source_tree.item(selection[0])
            source_id = item['tags'][0]
            source = self.source_manager.get_source(source_id)
            if source.get('type') == 'builtin':
                messagebox.showerror("错误", "内置来源不允许删除")
                return
            if messagebox.askyesno("确认删除", f"确定要删除来源 '{source['name']}' 吗?"):
                success, message = self.source_manager.delete_source(source_id)
                if success:
                    messagebox.showinfo("成功", message)
                    refresh_sources()
                else:
                    messagebox.showerror("错误", message)
        
        def add_source():
            """添加来源"""
            self.show_add_source_dialog(source_window, refresh_sources)
        
        ttk.Button(btn_frame, text="➕ 添加来源", command=add_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑️ 删除", command=delete_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🔄 刷新", command=refresh_sources).pack(side=tk.LEFT, padx=(0, 5))


def main():
    """主函数"""
    root = tk.Tk()
    app = SkillManagerGUI(root)

    
    # 窗口居中
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()







    def show_add_source_dialog(self, parent, callback=None):
        """显示添加来源对话框"""
        import tkinter.messagebox as messagebox
        
        dialog = tk.Toplevel(parent)
        dialog.title("添加Skill来源")
        dialog.geometry("600x300")
        
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        row = 0
        ttk.Label(main_frame, text="来源名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=50)
        name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(main_frame, text="仓库URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, width=50)
        url_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(例: https://github.com/user/repo)", 
                 font=('Arial', 8), foreground='gray').grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        ttk.Label(main_frame, text="描述:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(main_frame, width=50)
        desc_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(main_frame, text="Skill名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        skill_name_entry = ttk.Entry(main_frame, width=50)
        skill_name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        ttk.Label(main_frame, text="(可选,留空则使用仓库名)", 
                 font=('Arial', 8), foreground='gray').grid(row=row+1, column=1, sticky=tk.W)
        row += 2
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        def save():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            desc = desc_entry.get().strip()
            skill_name = skill_name_entry.get().strip()
            
            if not name or not url:
                messagebox.showerror("错误", "名称和URL不能为空")
                return
            
            # 从URL提取仓库名作为skill名称
            if not skill_name:
                skill_name = url.rstrip('/').split('/')[-1].replace('.git', '')
            
            skills = [{
                'name': skill_name,
                'url': url if url.endswith('.git') else url + '.git',
                'description': desc
            }]
            
            source_data = {
                'name': name,
                'url': url,
                'description': desc,
                'skills': skills
            }
            
            success, message = self.source_manager.add_source(source_data)
            if success:
                messagebox.showinfo("成功", message)
                dialog.destroy()
                if callback:
                    callback()
            else:
                messagebox.showerror("错误", message)
        
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def show_source_manager(self):
        """显示来源管理窗口"""
        # 创建来源管理窗口
        source_window = tk.Toplevel(self.root)
        source_window.title("Skill来源管理")
        source_window.geometry("700x500")
        source_window.resizable(True, True)
        
        # 主框架
        main_frame = ttk.Frame(source_window, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        source_window.columnconfigure(0, weight=1)
        source_window.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        
        # 来源列表
        ttk.Label(main_frame, text="Skill下载来源:", font=('Arial', 12, 'bold')).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # 创建Treeview显示来源
        columns = ('name', 'url', 'type')
        source_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=12)
        
        source_tree.heading('name', text='来源名称')
        source_tree.heading('url', text='仓库URL')
        source_tree.heading('type', text='类型')
        
        source_tree.column('name', width=200)
        source_tree.column('url', width=350)
        source_tree.column('type', width=80)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=source_tree.yview)
        source_tree.configure(yscrollcommand=scrollbar.set)
        
        source_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 加载来源数据
        def refresh_sources():
            # 清空列表
            for item in source_tree.get_children():
                source_tree.delete(item)
            
            # 重新加载
            self.source_manager.reload()
            sources = self.source_manager.list_sources()
            
            for source in sources:
                type_text = '内置' if source.get('type') == 'builtin' else '自定义'
                source_tree.insert('', tk.END, values=(
                    source['name'],
                    source['url'],
                    type_text
                ), tags=(source['id'],))
        
        refresh_sources()
        
        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, pady=(10, 0), sticky=tk.W)
        
        def add_source():
            """添加来源"""
            self.show_add_source_dialog(source_window, refresh_sources)
        
        def edit_source():
            """编辑来源"""
            selection = source_tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请先选择要编辑的来源")
                return
            
            # 获取选中的来源ID
            item = source_tree.item(selection[0])
            source_id = item['tags'][0]
            
            self.show_edit_source_dialog(source_window, source_id, refresh_sources)
        
        def delete_source():
            """删除来源"""
            selection = source_tree.selection()
            if not selection:
                messagebox.showwarning("提示", "请先选择要删除的来源")
                return
            
            # 获取选中的来源ID
            item = source_tree.item(selection[0])
            source_id = item['tags'][0]
            source = self.source_manager.get_source(source_id)
            
            if source.get('type') == 'builtin':
                messagebox.showerror("错误", "内置来源不允许删除")
                return
            
            # 确认删除
            if messagebox.askyesno("确认删除", f"确定要删除来源 '{source['name']}' 吗?"):
                success, message = self.source_manager.delete_source(source_id)
                if success:
                    messagebox.showinfo("成功", message)
                    refresh_sources()
                else:
                    messagebox.showerror("错误", message)
        
        ttk.Button(btn_frame, text="➕ 添加来源", command=add_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="✏️ 编辑", command=edit_source).pack(side=tk.LEFT, padx=(0, 5))
        def add_source():
            """添加来源"""
            self.show_add_source_dialog(source_window, refresh_sources)
        
        ttk.Button(btn_frame, text="➕ 添加来源", command=add_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🗑️ 删除", command=delete_source).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="🔄 刷新", command=refresh_sources).pack(side=tk.LEFT, padx=(0, 5))
    



    def show_add_source_dialog(self, parent, callback=None):
        """显示添加来源对话框"""
        dialog = tk.Toplevel(parent)
        dialog.title("添加Skill来源")
        dialog.geometry("600x400")
        dialog.resizable(False, False)
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 表单字段
        row = 0
        
        # 来源名称
        ttk.Label(main_frame, text="来源名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=50)
        name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 仓库URL
        ttk.Label(main_frame, text="仓库URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, width=50)
        url_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 描述
        ttk.Label(main_frame, text="描述:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(main_frame, width=50)
        desc_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Skills列表
        ttk.Label(main_frame, text="Skills:").grid(row=row, column=0, sticky=tk.NW, pady=5)
        
        skills_frame = ttk.Frame(main_frame)
        skills_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Skill输入框
        skill_entries = []
        
        def add_skill_entry():
            """添加skill输入框"""
            entry_frame = ttk.Frame(skills_frame)
            entry_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(entry_frame, text="名称:").pack(side=tk.LEFT)
            skill_name = ttk.Entry(entry_frame, width=15)
            skill_name.pack(side=tk.LEFT, padx=(5, 10))
            
            ttk.Label(entry_frame, text="URL:").pack(side=tk.LEFT)
            skill_url = ttk.Entry(entry_frame, width=30)
            skill_url.pack(side=tk.LEFT, padx=5)
            
            skill_entries.append((skill_name, skill_url))
        
        # 添加第一个skill输入框
        add_skill_entry()
        
        ttk.Button(skills_frame, text="+ 添加Skill", command=add_skill_entry).pack(anchor=tk.W, pady=(5, 0))
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row+1, column=0, columnspan=2, pady=(20, 0))
        
        def save():
            """保存来源"""
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            desc = desc_entry.get().strip()
            
            if not name or not url:
                messagebox.showerror("错误", "名称和URL不能为空")
                return
            
            # 收集skills
            skills = []
            for skill_name, skill_url in skill_entries:
                sn = skill_name.get().strip()
                su = skill_url.get().strip()
                if sn and su:
                    skills.append({
                        'name': sn,
                        'url': su,
                        'description': ''
                    })
            
            # 添加来源
            source_data = {
                'name': name,
                'url': url,
                'description': desc,
                'skills': skills
            }
            
            success, message = self.source_manager.add_source(source_data)
            if success:
                messagebox.showinfo("成功", message)
                dialog.destroy()
                if callback:
                    callback()
            else:
                messagebox.showerror("错误", message)
        
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_edit_source_dialog(self, parent, source_id, callback=None):
        """显示编辑来源对话框"""
        source = self.source_manager.get_source(source_id)
        if not source:
            messagebox.showerror("错误", "来源不存在")
            return
        
        if source.get('type') == 'builtin':
            messagebox.showerror("错误", "内置来源不允许编辑")
            return
        
        # 创建对话框(与添加对话框类似,但预填充数据)
        dialog = tk.Toplevel(parent)
        dialog.title("编辑Skill来源")
        dialog.geometry("600x400")
        dialog.resizable(False, False)
        
        # 主框架
        main_frame = ttk.Frame(dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 表单字段(预填充)
        row = 0
        
        ttk.Label(main_frame, text="来源名称:").grid(row=row, column=0, sticky=tk.W, pady=5)
        name_entry = ttk.Entry(main_frame, width=50)
        name_entry.insert(0, source['name'])
        name_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(main_frame, text="仓库URL:").grid(row=row, column=0, sticky=tk.W, pady=5)
        url_entry = ttk.Entry(main_frame, width=50)
        url_entry.insert(0, source['url'])
        url_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        ttk.Label(main_frame, text="描述:").grid(row=row, column=0, sticky=tk.W, pady=5)
        desc_entry = ttk.Entry(main_frame, width=50)
        desc_entry.insert(0, source.get('description', ''))
        desc_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(20, 0))
        
        def save():
            """保存修改"""
            source_data = {
                'name': name_entry.get().strip(),
                'url': url_entry.get().strip(),
                'description': desc_entry.get().strip(),
                'skills': source.get('skills', [])
            }
            
            success, message = self.source_manager.update_source(source_id, source_data)
            if success:
                messagebox.showinfo("成功", message)
                dialog.destroy()
                if callback:
                    callback()
            else:
                messagebox.showerror("错误", message)
        
        ttk.Button(btn_frame, text="保存", command=save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)


if __name__ == '__main__':

    main()
