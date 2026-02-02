/**
 * Chart Studio - 柱状图模块
 * 支持横向、纵向、对比等模式
 */

/**
 * 默认颜色调色板
 */
const COLOR_PALETTE = [
    '#6366F1', '#22C55E', '#F59E0B', '#EF4444', 
    '#06B6D4', '#8B5CF6', '#EC4899', '#14B8A6'
];

/**
 * 默认数据
 */
const DEFAULT_DATA = {
    labels: ['一月', '二月', '三月', '四月', '五月'],
    datasets: [
        {
            label: '系列 A',
            data: [65, 59, 80, 81, 56],
            backgroundColor: COLOR_PALETTE[0]
        },
        {
            label: '系列 B',
            data: [28, 48, 40, 19, 86],
            backgroundColor: COLOR_PALETTE[1]
        }
    ]
};

export class BarChart {
    constructor(canvasId, app) {
        this.canvasId = canvasId;
        this.app = app;
        this.chart = null;
        this.data = JSON.parse(JSON.stringify(DEFAULT_DATA));
        
        // 配置选项
        this.options = {
            indexAxis: 'x', // x: 纵向, y: 横向
            stacked: false, // 是否堆叠
            showLegend: true,
            showValues: false,
            grouped: true // 是否分组对比
        };
        
        this.init();
    }
    
    init() {
        this.createChart();
        this.renderControlPanel();
        this.bindEvents();
    }
    
    createChart() {
        const ctx = document.getElementById(this.canvasId);
        if (!ctx) return;
        
        const isDark = this.app.getTheme() === 'dark';
        const textColor = isDark ? '#F8FAFC' : '#0F172A';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(15, 23, 42, 0.1)';
        
        this.chart = new Chart(ctx, {
            type: 'bar',
            data: this.data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                indexAxis: this.options.indexAxis,
                plugins: {
                    legend: {
                        display: this.options.showLegend,
                        position: 'bottom',
                        labels: { color: textColor }
                    },
                    datalabels: { // 需要 chartjs-plugin-datalabels，暂且手写简单实现或忽略
                        display: this.options.showValues,
                        color: textColor,
                        anchor: 'end',
                        align: 'top'
                    }
                },
                scales: {
                    x: {
                        stacked: this.options.stacked,
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        stacked: this.options.stacked,
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    }
                },
                barPercentage: 0.8,
                categoryPercentage: 0.9
            }
        });
    }
    
    /**
     * 渲染属性面板控件
     */
    renderControlPanel() {
        const container = document.getElementById('bar-data-list');
        if (!container) return;
        
        // 这里简化实现，主要专注于配置面板的渲染
        // 实际项目应包含完整的数据编辑表格
    }
    
    bindEvents() {
        // 绑定配置变更事件
        const axisSelect = document.getElementById('bar-axis');
        const stackCheck = document.getElementById('bar-stacked');
        
        if (axisSelect) {
            axisSelect.addEventListener('change', (e) => {
                this.options.indexAxis = e.target.value;
                this.recreateChart();
            });
        }
        
        if (stackCheck) {
            stackCheck.addEventListener('change', (e) => {
                this.options.stacked = e.target.checked;
                this.recreateChart();
            });
        }
    }
    
    recreateChart() {
        if (this.chart) this.chart.destroy();
        this.createChart();
        if (this.app.saveToLocalStorage) this.app.saveToLocalStorage();
    }
    
    reset() {
        this.data = JSON.parse(JSON.stringify(DEFAULT_DATA));
        this.options.indexAxis = 'x';
        this.options.stacked = false;
        this.recreateChart();
        
        // 重置 UI
        const axisSelect = document.getElementById('bar-axis');
        const stackCheck = document.getElementById('bar-stacked');
        if (axisSelect) axisSelect.value = 'x';
        if (stackCheck) stackCheck.checked = false;
    }
    
    updateTheme() {
        this.recreateChart();
    }
    
    onActivate() {
        if (this.chart) this.chart.resize();
    }
    
    getCanvas() {
        return document.getElementById(this.canvasId);
    }
}
