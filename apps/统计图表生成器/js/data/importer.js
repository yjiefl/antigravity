/**
 * Chart Studio - 数据导入模块
 * 支持 JSON 和 CSV 格式的数据导入
 */

/**
 * 数据导入器类
 */
export class DataImporter {
    /**
     * 构造函数
     * @param {Object} app - 主应用实例
     */
    constructor(app) {
        this.app = app;
        this.currentFormat = 'json';
        
        this.bindEvents();
    }
    
    /**
     * 绑定事件
     */
    bindEvents() {
        // 格式切换标签
        document.querySelectorAll('.tab-btn[data-tab]').forEach(btn => {
            btn.addEventListener('click', () => {
                this.currentFormat = btn.dataset.tab;
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.updatePlaceholder();
            });
        });
        
        // 关闭弹窗
        const closeBtn = document.getElementById('close-import-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal());
        }
        
        // 点击背景关闭
        const modal = document.getElementById('import-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.hideModal();
            });
        }
        
        // 文件上传
        const uploadBtn = document.getElementById('btn-upload-file');
        const fileInput = document.getElementById('import-file');
        if (uploadBtn && fileInput) {
            uploadBtn.addEventListener('click', () => fileInput.click());
            fileInput.addEventListener('change', (e) => this.handleFileUpload(e));
        }
        
        // 应用数据
        const applyBtn = document.getElementById('btn-apply-import');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => this.applyData());
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
        const modal = document.getElementById('import-modal');
        if (modal) {
            modal.classList.remove('hidden');
            // 聚焦到文本区域
            const textarea = document.getElementById('import-data');
            if (textarea) textarea.focus();
        }
    }
    
    /**
     * 隐藏弹窗
     */
    hideModal() {
        const modal = document.getElementById('import-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }
    
    /**
     * 更新占位符文本
     */
    updatePlaceholder() {
        const textarea = document.getElementById('import-data');
        if (!textarea) return;
        
        if (this.currentFormat === 'json') {
            textarea.placeholder = `JSON 格式示例:
[
  {"label": "项目A", "value": 30, "color": "#6366f1"},
  {"label": "项目B", "value": 50, "color": "#22c55e"},
  {"label": "项目C", "value": 20, "color": "#f59e0b"}
]`;
        } else {
            textarea.placeholder = `CSV 格式示例:
标签,数值,颜色
项目A,30,#6366f1
项目B,50,#22c55e
项目C,20,#f59e0b`;
        }
    }
    
    /**
     * 处理文件上传
     * @param {Event} e - 文件选择事件
     */
    handleFileUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = (event) => {
            const textarea = document.getElementById('import-data');
            if (textarea) {
                textarea.value = event.target.result;
            }
            
            // 自动检测格式
            if (file.name.endsWith('.json')) {
                this.currentFormat = 'json';
            } else if (file.name.endsWith('.csv')) {
                this.currentFormat = 'csv';
            }
            
            // 更新标签状态
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.tab === this.currentFormat);
            });
        };
        reader.readAsText(file);
        
        // 清除文件选择，允许再次选择同一文件
        e.target.value = '';
    }
    
    /**
     * 应用导入的数据
     */
    applyData() {
        const textarea = document.getElementById('import-data');
        if (!textarea || !textarea.value.trim()) {
            this.showError('请输入或粘贴数据');
            return;
        }
        
        try {
            let data;
            if (this.currentFormat === 'json') {
                data = this.parseJSON(textarea.value);
            } else {
                data = this.parseCSV(textarea.value);
            }
            
            if (!data || data.length === 0) {
                this.showError('解析数据为空，请检查格式');
                return;
            }
            
            // 应用到当前图表
            const chart = this.app.getActiveChart();
            if (chart && typeof chart.setData === 'function') {
                chart.setData(data);
                this.hideModal();
                console.log('数据导入成功:', data);
            } else {
                this.showError('当前图表不支持数据导入');
            }
            
        } catch (error) {
            this.showError(`解析失败: ${error.message}`);
        }
    }
    
    /**
     * 解析 JSON 数据
     * @param {string} text - JSON 文本
     * @returns {Array} 解析后的数据数组
     */
    parseJSON(text) {
        const data = JSON.parse(text);
        
        if (!Array.isArray(data)) {
            throw new Error('JSON 数据必须是数组格式');
        }
        
        return data.map((item, index) => ({
            label: String(item.label || item.name || item.key || `项目 ${index + 1}`),
            value: parseFloat(item.value || item.val || item.count || 0),
            color: item.color || item.backgroundColor || null
        }));
    }
    
    /**
     * 解析 CSV 数据
     * @param {string} text - CSV 文本
     * @returns {Array} 解析后的数据数组
     */
    parseCSV(text) {
        const lines = text.trim().split('\n');
        if (lines.length < 2) {
            throw new Error('CSV 至少需要标题行和一行数据');
        }
        
        // 解析标题行
        const headers = this.parseCSVLine(lines[0]).map(h => h.toLowerCase().trim());
        
        // 查找列索引
        const labelIdx = headers.findIndex(h => 
            ['label', '标签', 'name', '名称', 'key'].includes(h)
        );
        const valueIdx = headers.findIndex(h => 
            ['value', '数值', 'val', 'count', '值', '数量'].includes(h)
        );
        const colorIdx = headers.findIndex(h => 
            ['color', '颜色', 'background', 'bg'].includes(h)
        );
        
        if (valueIdx === -1) {
            throw new Error('CSV 必须包含数值列（value 或 数值）');
        }
        
        // 解析数据行
        const data = [];
        for (let i = 1; i < lines.length; i++) {
            const line = lines[i].trim();
            if (!line) continue;
            
            const values = this.parseCSVLine(line);
            data.push({
                label: labelIdx >= 0 ? values[labelIdx] : `项目 ${i}`,
                value: parseFloat(values[valueIdx]) || 0,
                color: colorIdx >= 0 ? values[colorIdx] : null
            });
        }
        
        return data;
    }
    
    /**
     * 解析 CSV 单行
     * @param {string} line - CSV 行
     * @returns {Array} 解析后的值数组
     */
    parseCSVLine(line) {
        const result = [];
        let current = '';
        let inQuotes = false;
        
        for (let i = 0; i < line.length; i++) {
            const char = line[i];
            
            if (char === '"') {
                inQuotes = !inQuotes;
            } else if (char === ',' && !inQuotes) {
                result.push(current.trim());
                current = '';
            } else {
                current += char;
            }
        }
        result.push(current.trim());
        
        return result;
    }
    
    /**
     * 显示错误提示
     * @param {string} message - 错误消息
     */
    showError(message) {
        // 简单的错误提示，后续可以改为 Toast 组件
        alert(message);
    }
}
