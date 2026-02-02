/**
 * 储能自动调节系统 - 输入表单组件
 * 
 * 用于输入调节计算所需的参数
 */

import React from 'react';

/**
 * 输入表单组件
 * 
 * @param {Object} props - 组件属性
 * @param {Object} props.formData - 表单数据
 * @param {Function} props.onFormChange - 表单数据变化处理函数
 * @param {Function} props.onSubmit - 提交处理函数
 * @param {boolean} props.loading - 是否正在加载
 */
function InputForm({ formData, onFormChange, onSubmit, loading }) {
  
  /**
   * 处理输入框值变化
   * @param {string} field - 字段名
   * @param {Event} e - 事件对象
   */
  const handleChange = (field, e) => {
    const value = parseFloat(e.target.value) || 0;
    onFormChange({ ...formData, [field]: value });
  };

  /**
   * 处理表单提交
   * @param {Event} e - 事件对象
   */
  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit();
  };

  /**
   * 获取储能状态样式类名
   * @returns {string} 样式类名
   */
  const getStoragePowerClass = () => {
    if (formData.storage_power < 0) return 'form-input form-input--charging';
    if (formData.storage_power > 0) return 'form-input form-input--discharging';
    return 'form-input';
  };

  return (
    <div className="card">
      <div className="card__header">
        <div className="card__icon">⚡</div>
        <h2 className="card__title">参数输入</h2>
      </div>
      
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          {/* 储能当前出力 */}
          <div className="form-group">
            <label className="form-label">
              储能当前出力
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="0.1"
              className={getStoragePowerClass()}
              value={formData.storage_power}
              onChange={(e) => handleChange('storage_power', e)}
              placeholder="正值放电，负值充电"
            />
            <small style={{ color: 'var(--gray-500)', fontSize: '0.75rem' }}>
              {formData.storage_power < 0 ? '🔋 充电中' : formData.storage_power > 0 ? '⚡ 放电中' : '💤 待机'}
            </small>
          </div>
          
          {/* 调度指令值 */}
          <div className="form-group">
            <label className="form-label">
              调度指令值 (AGC)
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="0.1"
              className="form-input"
              value={formData.dispatch_target}
              onChange={(e) => handleChange('dispatch_target', e)}
              placeholder="输入调度下达的发电计划"
            />
          </div>
          
          {/* 光伏出力 */}
          <div className="form-group">
            <label className="form-label">
              光伏出力
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              className="form-input"
              value={formData.pv_power}
              onChange={(e) => handleChange('pv_power', e)}
              placeholder="输入光伏电站当前出力"
            />
          </div>
          
          {/* 当前SOC */}
          <div className="form-group">
            <label className="form-label">
              当前 SOC
              <span className="form-label__unit">(%)</span>
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              max="100"
              className="form-input"
              value={formData.soc}
              onChange={(e) => handleChange('soc', e)}
              placeholder="储能剩余电量百分比"
            />
            {/* SOC 进度条 */}
            <div className="soc-bar">
              <div 
                className={`soc-bar__fill ${
                  formData.soc < 20 ? 'soc-bar__fill--low' : 
                  formData.soc < 50 ? 'soc-bar__fill--medium' : 
                  'soc-bar__fill--high'
                }`}
                style={{ width: `${Math.min(100, Math.max(0, formData.soc))}%` }}
              />
            </div>
          </div>
          
          {/* 充电上限 */}
          <div className="form-group">
            <label className="form-label">
              充电上限
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="1"
              max="0"
              className="form-input"
              value={formData.charge_limit}
              onChange={(e) => handleChange('charge_limit', e)}
              placeholder="负值，如 -50"
            />
          </div>
          
          {/* 放电上限 */}
          <div className="form-group">
            <label className="form-label">
              放电上限
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="1"
              min="0"
              className="form-input"
              value={formData.discharge_limit}
              onChange={(e) => handleChange('discharge_limit', e)}
              placeholder="正值，如 50"
            />
          </div>
          
          {/* 死区值 */}
          <div className="form-group">
            <label className="form-label">
              死区值
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="0.1"
              min="0"
              className="form-input"
              value={formData.dead_zone}
              onChange={(e) => handleChange('dead_zone', e)}
              placeholder="偏差小于此值不调节"
            />
          </div>

          {/* 调节步长 */}
          <div className="form-group">
            <label className="form-label">
              调节步长
              <span className="form-label__unit">(MW)</span>
            </label>
            <input
              type="number"
              step="0.5"
              min="0"
              className="form-input"
              value={formData.step_size}
              onChange={(e) => handleChange('step_size', e)}
              placeholder="单次调节限制"
            />
          </div>
          
          {/* 实际值输入（全宽） */}
          <div className="form-group form-group--full" style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '8px', border: '1px dashed var(--gray-700)', marginTop: '0.5rem' }}>
            <div className="form-label" style={{ marginBottom: '0.75rem', color: 'var(--primary-300)' }}>🔍 实际值监测（可选）</div>
            <div className="form-grid">
              <div className="form-group">
                <label className="form-label">
                  储能实际输出
                  <span className="form-label__unit">(MW)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  className="form-input"
                  value={formData.actual_storage_power}
                  onChange={(e) => handleChange('actual_storage_power', e)}
                  placeholder="反馈实际输出"
                />
              </div>
              <div className="form-group">
                <label className="form-label">
                  光伏实际输出
                  <span className="form-label__unit">(MW)</span>
                </label>
                <input
                  type="number"
                  step="0.1"
                  className="form-input"
                  value={formData.actual_pv_power}
                  onChange={(e) => handleChange('actual_pv_power', e)}
                  placeholder="反馈实际输出"
                />
              </div>
            </div>
          </div>
          
          {/* SOC 下限 */}
          <div className="form-group">
            <label className="form-label">
              SOC 下限
              <span className="form-label__unit">(%)</span>
            </label>
            <input
              type="number"
              step="1"
              min="0"
              max="100"
              className="form-input"
              value={formData.soc_min}
              onChange={(e) => handleChange('soc_min', e)}
              placeholder="如 8%"
            />
          </div>
          
          {/* 提交按钮 */}
          <div className="form-group form-group--full">
            <button 
              type="submit" 
              className="btn btn--primary btn--block"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="loading__spinner"></span>
                  计算中...
                </>
              ) : (
                <>
                  📊 计算调节策略
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

export default InputForm;
