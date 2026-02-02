/**
 * Chart Studio - 折线图模块
 * 支持普通折线、面积图、堆积图
 */

const COLOR_PALETTE = [
    '#6366F1', '#22C55E', '#F59E0B', '#EF4444', 
    '#06B6D4', '#8B5CF6'
];

const DEFAULT_DATA = {
    labels: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    datasets: [
        {
            label: '访问量',
            data: [120, 132, 101, 134, 90, 230, 210],
            borderColor: COLOR_PALETTE[0],
            backgroundColor: 'rgba(99, 102, 241, 0.2)', // 透明度颜色
            fill: false,
            tension: 0.4
        },
        {
            label: '订单量',
            data: [220, 182, 191, 234, 290, 330, 310],
            borderColor: COLOR_PALETTE[1],
            backgroundColor: 'rgba(34, 197, 94, 0.2)',
            fill: false,
            tension: 0.4
        }
    ]
};

export class LineChart {
    constructor(canvasId, app) {
        this.canvasId = canvasId;
        this.app = app;
        this.chart = null;
        this.data = JSON.parse(JSON.stringify(DEFAULT_DATA));
        
        this.options = {
            area: false,      // 面积图
            stacked: false,   // 堆积
            smooth: true,     // 平滑曲线
            showPoints: true
        };
        
        this.init();
    }
    
    init() {
        this.createChart();
        this.bindEvents();
    }
    
    createChart() {
        const ctx = document.getElementById(this.canvasId);
        if (!ctx) return;
        
        const isDark = this.app.getTheme() === 'dark';
        const textColor = isDark ? '#F8FAFC' : '#0F172A';
        const gridColor = isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(15, 23, 42, 0.1)';
        
        // 应用配置
        this.data.datasets.forEach(bs => {
            bs.fill = this.options.area ? (this.options.stacked ? 'origin' : true) : false;
            bs.tension = this.options.smooth ? 0.4 : 0;
            bs.pointRadius = this.options.showPoints ? 4 : 0;
        });
        
        this.chart = new Chart(ctx, {
            type: 'line',
            data: this.data,
            options: {
                responsive: true,
                maintainAspectRatio: true,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    },
                    y: {
                        stacked: this.options.stacked,
                        grid: { color: gridColor },
                        ticks: { color: textColor }
                    }
                },
                plugins: {
                    legend: {
                        labels: { color: textColor, position: 'bottom' }
                    }
                }
            }
        });
    }
    
    bindEvents() {
        const areaCheck = document.getElementById('line-area');
        const smoothCheck = document.getElementById('line-smooth');
        const stackedCheck = document.getElementById('line-stacked');
        
        if (areaCheck) {
            areaCheck.addEventListener('change', (e) => {
                this.options.area = e.target.checked;
                this.recreateChart();
            });
        }
        
        if (smoothCheck) {
            smoothCheck.addEventListener('change', (e) => {
                this.options.smooth = e.target.checked;
                this.recreateChart();
            });
        }
        
        if (stackedCheck) {
            stackedCheck.addEventListener('change', (e) => {
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
    
    updateTheme() {
        this.recreateChart();
    }
    
    onActivate() {
        if (this.chart) this.chart.resize();
    }
    
    reset() {
        this.data = JSON.parse(JSON.stringify(DEFAULT_DATA));
        this.options = { area: false, stacked: false, smooth: true, showPoints: true };
        this.recreateChart();
        
        // UI Reset
        if(document.getElementById('line-area')) document.getElementById('line-area').checked = false;
        if(document.getElementById('line-smooth')) document.getElementById('line-smooth').checked = true;
        if(document.getElementById('line-stacked')) document.getElementById('line-stacked').checked = false;
    }
    
    getCanvas() {
        return document.getElementById(this.canvasId);
    }
}
