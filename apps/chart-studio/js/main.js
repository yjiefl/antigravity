/**
 * Chart Studio - 主应用入口
 * 负责初始化应用、协调各模块、处理主题切换
 */

import { PieChart } from './charts/pie.js';
import { BarChart } from './charts/bar.js';
import { LineChart } from './charts/line.js';
import { DataImporter } from './data/importer.js';
import { ChartExporter } from './export/exporter.js';

/**
 * 应用主类
 * 管理所有图表模块和用户交互
 */
class ChartStudioApp {
    constructor() {
        // 当前活动的图表类型
        this.activeChartType = 'pie';
        
        // 当前主题（dark/light）
        this.currentTheme = 'dark';
        
        // 图表模块实例
        this.charts = {};
        
        // 工具实例
        this.importer = null;
        this.exporter = null;
        
        // 初始化应用
        this.init();
    }
    
    /**
     * 初始化应用
     */
    init() {
        // 加载保存的主题偏好
        this.loadThemePreference();
        
        // 初始化各图表模块
        this.initCharts();
        
        // 初始化工具
        this.importer = new DataImporter(this);
        this.exporter = new ChartExporter(this);
        
        // 绑定事件
        this.bindEvents();
        
        // 显示默认数据或加载存档
        if (!this.loadFromLocalStorage()) {
            this.switchChart('pie');
        }
        
        console.log('Chart Studio 初始化完成');
    }
    
    /**
     * 初始化所有图表模块
     */
    initCharts() {
        this.charts = {
            pie: new PieChart('pie-canvas', this),
            bar: new BarChart('bar-canvas', this),
            line: new LineChart('line-canvas', this)
        };
    }
    
    /**
     * 绑定全局事件
     */
    bindEvents() {
        // 图表类型切换按钮
        document.querySelectorAll('.nav-btn[data-type]').forEach(btn => {
            btn.addEventListener('click', () => {
                const type = btn.dataset.type;
                this.switchChart(type);
            });
        });
        
        // 主题切换
        const themeBtn = document.getElementById('btn-theme');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => this.toggleTheme());
        }
        
        // 导入按钮
        const importBtn = document.getElementById('btn-import');
        if (importBtn) {
            importBtn.addEventListener('click', () => this.importer.showModal());
        }
        
        // 导出按钮
        const exportBtn = document.getElementById('btn-export');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exporter.showModal());
        }
        
        // 重置按钮
        const resetBtn = document.getElementById('btn-reset');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetCurrentChart());
        }
        
        // 全屏按钮
        const fullscreenBtn = document.getElementById('btn-fullscreen');
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }

        // 存档按钮
        const saveBtn = document.getElementById('btn-save-archive');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveArchive());
        }

        // 读取按钮
        const loadBtn = document.getElementById('btn-load-archive');
        if (loadBtn) {
            loadBtn.addEventListener('click', () => this.loadArchive());
        }
        
        // 监听系统主题变化
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            if (!localStorage.getItem('chart-studio-theme')) {
                this.setTheme(e.matches ? 'dark' : 'light');
            }
        });

        // 宽面板切换
        const widthToggleBtn = document.getElementById('btn-toggle-panel-width');
        if (widthToggleBtn) {
            widthToggleBtn.addEventListener('click', () => {
                document.body.classList.toggle('panel-wide');
                // 触发图表重绘以适应新尺寸
                const chart = this.getActiveChart();
                if (chart && chart.onActivate) chart.onActivate();
            });
        }

        // 快速保存到网页按钮
        const quickSaveBtn = document.getElementById('btn-quick-save');
        if (quickSaveBtn) {
            quickSaveBtn.addEventListener('click', () => {
                const name = prompt('请输入存档名称:', `项目 ${new Date().toLocaleString()}`);
                if (name !== null) {
                    this.saveProject(name || `未命名项目 ${new Date().toLocaleString()}`);
                }
            });
        }

        // 项目管理弹窗
        const projectsBtn = document.getElementById('btn-projects');
        const projectsModal = document.getElementById('projects-modal');
        const closeProjectsBtn = document.getElementById('close-projects-modal');
        
        if (projectsBtn && projectsModal) {
            projectsBtn.addEventListener('click', () => {
                this.renderProjectsList();
                projectsModal.classList.remove('hidden');
            });
        }

        if (closeProjectsBtn && projectsModal) {
            closeProjectsBtn.addEventListener('click', () => projectsModal.classList.add('hidden'));
        }

        const saveCurrentBtn = document.getElementById('btn-save-current');
        if (saveCurrentBtn) {
            saveCurrentBtn.addEventListener('click', () => {
                const nameInput = document.getElementById('new-project-name');
                const name = nameInput.value.trim() || `未命名项目 ${new Date().toLocaleString()}`;
                this.saveProject(name);
                nameInput.value = '';
                this.renderProjectsList();
            });
        }
    }

    /**
     * 切换主题
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.setTheme(newTheme);
    }
    
    /**
     * 切换图表类型
     * @param {string} type - 图表类型 (pie/flow/mind/electric)
     */
    switchChart(type) {
        this.activeChartType = type;
        
        // 更新导航按钮状态
        document.querySelectorAll('.nav-btn[data-type]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.type === type);
        });
        
        // 更新标题
        const titles = {
            pie: '饼图编辑器',
            bar: '柱状图编辑器',
            line: '折线图编辑器'
        };
        document.getElementById('chart-title').textContent = titles[type] || '图表编辑器';
        
        // 切换画布显示
        document.querySelectorAll('.chart-wrapper').forEach(wrapper => {
            wrapper.classList.add('hidden');
        });
        const activeWrapper = document.getElementById(`${type}-wrapper`);
        if (activeWrapper) {
            activeWrapper.classList.remove('hidden');
        }
        
        // 切换属性面板显示
        document.querySelectorAll('.panel-section').forEach(section => {
            section.classList.add('hidden');
        });
        const activePanel = document.getElementById(`${type}-properties`);
        if (activePanel) {
            activePanel.classList.remove('hidden');
        }
        
        // 通知对应的图表模块
        if (this.charts[type] && typeof this.charts[type].onActivate === 'function') {
            this.charts[type].onActivate();
        }
    }
    
    /**
     * 获取当前活动的图表实例
     * @returns {Object} 当前图表实例
     */
    getActiveChart() {
        return this.charts[this.activeChartType];
    }
    
    /**
     * 重置当前图表
     */
    resetCurrentChart() {
        const chart = this.getActiveChart();
        if (chart && typeof chart.reset === 'function') {
            chart.reset();
        }
    }
    
    /**
     * 设置主题
     * @param {string} theme - 主题名称 (dark/light)
     */
    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        
        // 更新主题按钮图标
        const themeBtn = document.getElementById('btn-theme');
        if (themeBtn) {
            const icon = themeBtn.querySelector('.btn-icon');
            const text = themeBtn.querySelector('span:last-child');
            if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
            if (text) text.textContent = theme === 'dark' ? '浅色模式' : '深色模式';
        }
        
        // 保存偏好与完整状态
        localStorage.setItem('chart-studio-theme', theme);
        this.saveToLocalStorage();
        
        // 通知所有图表更新主题
        Object.values(this.charts).forEach(chart => {
            if (typeof chart.updateTheme === 'function') {
                chart.updateTheme(theme);
            }
        });
    }
    
    /**
     * 加载保存的主题偏好
     */
    loadThemePreference() {
        const savedTheme = localStorage.getItem('chart-studio-theme');
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            // 使用系统偏好
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.setTheme(prefersDark ? 'dark' : 'light');
        }
    }
    
    /**
     * 切换全屏模式
     */
    toggleFullscreen() {
        const container = document.getElementById('canvas-container');
        if (!document.fullscreenElement) {
            container.requestFullscreen?.() || container.webkitRequestFullscreen?.();
        } else {
            document.exitFullscreen?.() || document.webkitExitFullscreen?.();
        }
    }
    
    /**
     * 保存存档到本地存储
     */
    saveArchive() {
        const archiveData = {
            activeChartType: this.activeChartType,
            theme: this.currentTheme,
            charts: {}
        };

        // 获取每个图表的数据和配置
        Object.keys(this.charts).forEach(type => {
            const chart = this.charts[type];
            archiveData.charts[type] = {
                data: chart.data,
                options: chart.options
            };
        });

        const blob = new Blob([JSON.stringify(archiveData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `chart-studio-archive-${new Date().getTime()}.json`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        console.log('存档已导出');
    }

    /**
     * 从本地文件读取存档
     */
    loadArchive() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (event) => {
                try {
                    const archiveData = JSON.parse(event.target.result);
                    
                    // 应用主题
                    if (archiveData.theme) this.setTheme(archiveData.theme);
                    
                    // 应用各图表数据
                    Object.keys(archiveData.charts).forEach(type => {
                        if (this.charts[type]) {
                            const chartData = archiveData.charts[type];
                            this.charts[type].data = chartData.data;
                            this.charts[type].options = chartData.options;
                            
                            // 更新 UI 控制器
                            if (type === 'pie') {
                                this.updatePieUI(chartData.options);
                            }
                            
                            this.charts[type].recreateChart();
                        }
                    });

                    // 切换回上次保存的图表类型
                    if (archiveData.activeChartType) {
                        this.switchChart(archiveData.activeChartType);
                    }

                    alert('存档读取成功！');
                } catch (err) {
                    console.error('读取存档失败:', err);
                    alert('存档文件格式错误');
                }
            };
            reader.readAsText(file);
        };
        input.click();
    }

    /**
     * 更新饼图 UI 组件的状态以匹配加载的选项
     */
    updatePieUI(options) {
        if (!options) return;
        const styleType = document.getElementById('pie-style-type');
        const cutoutSlider = document.getElementById('pie-cutout');
        const rotationSlider = document.getElementById('pie-rotation');
        const legendCheckbox = document.getElementById('pie-show-legend');
        const legendPosSelect = document.getElementById('pie-legend-position');
        const valueCheckbox = document.getElementById('pie-show-values');
        const showPercentCheckbox = document.getElementById('pie-show-percentage');
        const textColorInput = document.getElementById('pie-text-color');

        if (styleType) styleType.value = options.type || 'pie';
        if (cutoutSlider) {
            cutoutSlider.value = options.cutout || 0;
            document.getElementById('pie-cutout-value').textContent = `${options.cutout || 0}%`;
        }
        if (rotationSlider) {
            rotationSlider.value = options.rotation || 0;
            document.getElementById('pie-rotation-value').textContent = `${options.rotation || 0}°`;
        }
        if (legendCheckbox) legendCheckbox.checked = options.showLegend;
        if (legendPosSelect) legendPosSelect.value = options.legendPosition || 'bottom';
        if (valueCheckbox) valueCheckbox.checked = options.showValues;
        if (showPercentCheckbox) showPercentCheckbox.checked = options.showPercentage;
        if (textColorInput) textColorInput.value = options.textColor || (this.currentTheme === 'dark' ? '#F8FAFC' : '#0F172A');

        const unitInput = document.getElementById('pie-unit');
        if (unitInput) unitInput.value = options.unit || '';

        const floatingToggle = document.getElementById('pie-show-floating');
        if (floatingToggle) floatingToggle.checked = options.showFloatingLabels !== false;

        const fontSizeSlider = document.getElementById('pie-label-font-size');
        if (fontSizeSlider) {
            fontSizeSlider.value = options.floatingLabelFontSize || 13;
            document.getElementById('pie-label-font-size-val').textContent = `${fontSizeSlider.value}px`;
        }

        const paddingSlider = document.getElementById('pie-label-padding');
        if (paddingSlider) {
            paddingSlider.value = options.floatingLabelPadding || 8;
            document.getElementById('pie-label-padding-val').textContent = `${paddingSlider.value}px`;
        }

        const labelBgColorInput = document.getElementById('pie-label-bg-color');
        if (labelBgColorInput) labelBgColorInput.value = options.floatingLabelBgColor || '#1E293B';

        const labelBgOpacitySlider = document.getElementById('pie-label-bg-opacity');
        if (labelBgOpacitySlider) {
            labelBgOpacitySlider.value = (options.floatingLabelBgOpacity || 0.9) * 100;
            document.getElementById('pie-label-bg-opacity-val').textContent = `${labelBgOpacitySlider.value}%`;
        }
    }

    /**
     * 保存当前状态到浏览器本地存储
     */
    saveToLocalStorage() {
        const state = {
            activeChartType: this.activeChartType,
            theme: this.currentTheme,
            charts: {}
        };

        Object.keys(this.charts).forEach(type => {
            const chart = this.charts[type];
            state.charts[type] = {
                data: chart.data,
                options: chart.options
            };
        });

        localStorage.setItem('chart-studio-state', JSON.stringify(state));
    }

    /**
     * 从浏览器本地存储加载状态
     */
    loadFromLocalStorage() {
        const savedState = localStorage.getItem('chart-studio-state');
        if (!savedState) return false;

        try {
            const state = JSON.parse(savedState);
            this.currentTheme = state.theme || 'dark';
            this.setTheme(this.currentTheme);

            Object.keys(state.charts).forEach(type => {
                if (this.charts[type]) {
                    this.charts[type].data = state.charts[type].data;
                    this.charts[type].options = state.charts[type].options;
                }
            });

            this.switchChart(state.activeChartType || 'pie');
            
            // 更新 UI
            if (this.charts['pie']) {
                this.updatePieUI(this.charts['pie'].options);
            }
            
            return true;
        } catch (err) {
            console.error('加载本地存储失败:', err);
            return false;
        }
    }

    /**
     * 获取存档列表
     */
    getProjects() {
        const projects = localStorage.getItem('chart-studio-projects');
        return projects ? JSON.parse(projects) : [];
    }

    /**
     * 保存项目
     */
    saveProject(name) {
        const projects = this.getProjects();
        const newState = {
            id: Date.now(),
            name: name,
            date: new Date().toLocaleString(),
            activeChartType: this.activeChartType,
            theme: this.currentTheme,
            charts: {}
        };

        Object.keys(this.charts).forEach(type => {
            const chart = this.charts[type];
            newState.charts[type] = {
                data: chart.data,
                options: chart.options
            };
        });

        projects.unshift(newState);
        localStorage.setItem('chart-studio-projects', JSON.stringify(projects));
        alert(`项目 "${name}" 已保存！`);
    }

    /**
     * 渲染项目列表
     */
    renderProjectsList() {
        const listContainer = document.getElementById('projects-list');
        if (!listContainer) return;

        const projects = this.getProjects();
        listContainer.innerHTML = '';

        if (projects.length === 0) {
            listContainer.innerHTML = '<p class="text-muted" style="grid-column: 1/-1; text-align: center; padding: 2rem;">暂无已保存项目</p>';
            return;
        }

        projects.forEach(project => {
            const card = document.createElement('div');
            card.className = 'project-card';
            card.innerHTML = `
                <div class="project-info">
                    <div class="project-name">${project.name}</div>
                    <div class="project-meta">类型: ${project.activeChartType} | 修改时间: ${project.date}</div>
                </div>
                <div class="project-card-actions">
                    <button class="action-btn primary btn-load-proj" data-id="${project.id}">加载</button>
                    <button class="action-btn btn-delete-proj" data-id="${project.id}" style="color: var(--color-error)">删除</button>
                </div>
            `;
            listContainer.appendChild(card);
        });

        // 绑定事件
        listContainer.querySelectorAll('.btn-load-proj').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = parseInt(btn.dataset.id);
                this.loadProject(id);
                document.getElementById('projects-modal').classList.add('hidden');
            });
        });

        listContainer.querySelectorAll('.btn-delete-proj').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = parseInt(btn.dataset.id);
                if (confirm('确定要删除这个存档吗？')) {
                    this.deleteProject(id);
                    this.renderProjectsList();
                }
            });
        });
    }

    /**
     * 加载特定项目
     */
    loadProject(id) {
        const projects = this.getProjects();
        const project = projects.find(p => p.id === id);
        if (!project) return;

        this.currentTheme = project.theme || 'dark';
        this.setTheme(this.currentTheme);

        Object.keys(project.charts).forEach(type => {
            if (this.charts[type]) {
                this.charts[type].data = project.charts[type].data;
                this.charts[type].options = project.charts[type].options;
                this.charts[type].recreateChart();
            }
        });

        this.switchChart(project.activeChartType || 'pie');
        if (project.activeChartType === 'pie') {
            this.updatePieUI(project.charts['pie'].options);
        }
        
        this.saveToLocalStorage(); // 同步到当前活跃状态
    }

    /**
     * 删除项目
     */
    deleteProject(id) {
        let projects = this.getProjects();
        projects = projects.filter(p => p.id !== id);
        localStorage.setItem('chart-studio-projects', JSON.stringify(projects));
    }

    /**
     * 获取当前主题
     * @returns {string} 当前主题
     */
    getTheme() {
        return this.currentTheme;
    }
}

// 应用启动
document.addEventListener('DOMContentLoaded', () => {
    window.chartStudio = new ChartStudioApp();
});
