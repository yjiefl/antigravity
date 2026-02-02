/**
 * Chart Studio - 图表导出模块
 * 支持 PNG 和 SVG 格式导出，支持深色/浅色主题
 */

/**
 * 图表导出器类
 */
export class ChartExporter {
    /**
     * 构造函数
     * @param {Object} app - 主应用实例
     */
    constructor(app) {
        this.app = app;
        this.bindEvents();
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 关闭弹窗
        const closeBtn = document.getElementById('close-export-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal());
        }
        
        // 点击背景关闭
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.hideModal();
            });
        }
        
        // PNG 导出
        const pngBtn = document.getElementById('btn-export-png');
        if (pngBtn) {
            pngBtn.addEventListener('click', () => this.exportPNG());
        }
        
        // SVG 导出
        const svgBtn = document.getElementById('btn-export-svg');
        if (svgBtn) {
            svgBtn.addEventListener('click', () => this.exportSVG());
        }
        
        // JPG 导出
        const jpgBtn = document.getElementById('btn-export-jpg');
        if (jpgBtn) {
            jpgBtn.addEventListener('click', () => this.exportJPG());
        }
        
        // ESC 关闭弹窗
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideModal();
            }
        });
    }
    
    /**
     * 显示弹窗
     */
    showModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.classList.remove('hidden');
        }
    }
    
    /**
     * 隐藏弹窗
     */
    hideModal() {
        const modal = document.getElementById('export-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    /**
     * 导出为 PNG
     */
    async exportPNG() {
        const chartType = this.app.activeChartType;
        const chart = this.app.getActiveChart();
        
        if (!chart) {
            alert('无法获取当前图表');
            return;
        }
        
        try {
            let canvas;
            
            if (chartType === 'pie') {
                // Chart.js 图表直接使用 canvas
                canvas = chart.getCanvas();
            } else {
                // SVG 图表需要先转换为 canvas
                const svg = chart.getSVG();
                canvas = await this.svgToCanvas(svg);
            }
            
            if (!canvas) {
                throw new Error('无法获取画布');
            }
            
            // 导出图片
            const dataUrl = canvas.toDataURL('image/png', 1.0);
            this.downloadFile(dataUrl, `chart-${chartType}-${this.getTimestamp()}.png`);
            
            this.hideModal();
            console.log('PNG 导出成功');
            
        } catch (error) {
            console.error('PNG 导出失败:', error);
            alert(`导出失败: ${error.message}`);
        }
    }
    
    /**
     * 导出为 JPG
     */
    async exportJPG() {
        const chartType = this.app.activeChartType;
        const chart = this.app.getActiveChart();
        
        if (!chart) {
            alert('无法获取当前图表');
            return;
        }
        
        try {
            const canvas = chart.getCanvas();
            if (!canvas) throw new Error('无法获取画布');

            // 创建一个新的 canvas 来绘制背景，因为 JPG 不支持透明
            const outCanvas = document.createElement('canvas');
            outCanvas.width = canvas.width;
            outCanvas.height = canvas.height;
            const ctx = outCanvas.getContext('2d');

            // 绘制背景
            const isDark = this.app.getTheme() === 'dark';
            ctx.fillStyle = isDark ? '#0F172A' : '#F8FAFC';
            ctx.fillRect(0, 0, outCanvas.width, outCanvas.height);

            // 绘制图表
            ctx.drawImage(canvas, 0, 0);

            // 导出
            const dataUrl = outCanvas.toDataURL('image/jpeg', 0.9);
            this.downloadFile(dataUrl, `chart-${chartType}-${this.getTimestamp()}.jpg`);
            
            this.hideModal();
            console.log('JPG 导出成功');
        } catch (error) {
            console.error('JPG 导出失败:', error);
            alert(`导出失败: ${error.message}`);
        }
    }

    /**
     * 导出为 SVG
     */
    exportSVG() {
        const chartType = this.app.activeChartType;
        const chart = this.app.getActiveChart();
        
        if (!chart) {
            alert('无法获取当前图表');
            return;
        }
        
        try {
            let svgContent;
            
            if (chartType === 'pie') {
                // Chart.js 不支持直接导出 SVG，需要转换
                svgContent = this.canvasToSVG(chart.getCanvas());
            } else {
                // 直接获取 SVG 内容
                const svg = chart.getSVG();
                svgContent = this.prepareSVGForExport(svg);
            }
            
            if (!svgContent) {
                throw new Error('无法生成 SVG');
            }
            
            // 创建 Blob 并下载
            const blob = new Blob([svgContent], { type: 'image/svg+xml' });
            const url = URL.createObjectURL(blob);
            this.downloadFile(url, `chart-${chartType}-${this.getTimestamp()}.svg`);
            URL.revokeObjectURL(url);
            
            this.hideModal();
            console.log('SVG 导出成功');
            
        } catch (error) {
            console.error('SVG 导出失败:', error);
            alert(`导出失败: ${error.message}`);
        }
    }
    
    /**
     * SVG 转 Canvas
     * @param {SVGElement} svg - SVG 元素
     * @returns {Promise<HTMLCanvasElement>}
     */
    async svgToCanvas(svg) {
        return new Promise((resolve, reject) => {
            const svgData = new XMLSerializer().serializeToString(svg);
            const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
            const url = URL.createObjectURL(svgBlob);
            
            const img = new Image();
            img.onload = () => {
                // 创建高分辨率 canvas
                const scale = 2;
                const canvas = document.createElement('canvas');
                canvas.width = svg.clientWidth * scale;
                canvas.height = svg.clientHeight * scale;
                
                const ctx = canvas.getContext('2d');
                ctx.scale(scale, scale);
                
                // 绘制背景
                const isDark = this.app.getTheme() === 'dark';
                ctx.fillStyle = isDark ? '#0F172A' : '#F8FAFC';
                ctx.fillRect(0, 0, svg.clientWidth, svg.clientHeight);
                
                // 绘制 SVG
                ctx.drawImage(img, 0, 0);
                
                URL.revokeObjectURL(url);
                resolve(canvas);
            };
            img.onerror = () => {
                URL.revokeObjectURL(url);
                reject(new Error('SVG 加载失败'));
            };
            img.src = url;
        });
    }
    
    /**
     * Canvas 转 SVG（简化版）
     * @param {HTMLCanvasElement} canvas - Canvas 元素
     * @returns {string} SVG 字符串
     */
    canvasToSVG(canvas) {
        const isDark = this.app.getTheme() === 'dark';
        const bgColor = isDark ? '#0F172A' : '#F8FAFC';
        
        // 获取 canvas 图像数据
        const dataUrl = canvas.toDataURL('image/png');
        
        return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" 
     width="${canvas.width}" height="${canvas.height}" viewBox="0 0 ${canvas.width} ${canvas.height}">
    <rect width="100%" height="100%" fill="${bgColor}"/>
    <image x="0" y="0" width="${canvas.width}" height="${canvas.height}" xlink:href="${dataUrl}"/>
</svg>`;
    }
    
    /**
     * 准备 SVG 以供导出
     * @param {SVGElement} svg - 原始 SVG
     * @returns {string} 完整的 SVG 字符串
     */
    prepareSVGForExport(svg) {
        const isDark = this.app.getTheme() === 'dark';
        const bgColor = isDark ? '#0F172A' : '#F8FAFC';
        
        // 克隆 SVG
        const clone = svg.cloneNode(true);
        
        // 设置尺寸
        const width = svg.clientWidth || 900;
        const height = svg.clientHeight || 600;
        clone.setAttribute('width', width);
        clone.setAttribute('height', height);
        clone.setAttribute('viewBox', `0 0 ${width} ${height}`);
        
        // 添加背景
        const bgRect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        bgRect.setAttribute('width', '100%');
        bgRect.setAttribute('height', '100%');
        bgRect.setAttribute('fill', bgColor);
        clone.insertBefore(bgRect, clone.firstChild);
        
        // 添加 XML 声明和命名空间
        const svgString = new XMLSerializer().serializeToString(clone);
        return `<?xml version="1.0" encoding="UTF-8"?>\n${svgString}`;
    }
    
    /**
     * 下载文件
     * @param {string} url - 文件 URL 或 Data URL
     * @param {string} filename - 文件名
     */
    downloadFile(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
    
    /**
     * 获取时间戳字符串
     * @returns {string} 格式化的时间戳
     */
    getTimestamp() {
        const now = new Date();
        return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`;
    }
}
