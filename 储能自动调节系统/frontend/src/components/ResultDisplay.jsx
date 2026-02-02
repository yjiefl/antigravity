/**
 * 储能自动调节系统 - 结果展示组件
 * 
 * 展示调节计算的结果和建议
 */

import React from 'react';

/**
 * 结果展示组件
 * 
 * @param {Object} props - 组件属性
 * @param {Object} props.result - 计算结果数据
 */
function ResultDisplay({ result }) {
  if (!result) {
    return (
      <div className="card">
        <div className="card__header">
          <div className="card__icon">📈</div>
          <h2 className="card__title">调节结果</h2>
        </div>
        <div className="empty-state">
          <div className="empty-state__icon">📊</div>
          <div className="empty-state__title">等待计算</div>
          <div className="empty-state__description">请在左侧输入参数并点击计算</div>
        </div>
      </div>
    );
  }

  /**
   * 获取结果状态类型
   * @returns {string} 状态类型
   */
  const getStatusType = () => {
    if (result.conditions.is_curtailed) return 'danger';
    if (!result.need_adjust) return 'success';
    return 'warning';
  };

  /**
   * 获取状态图标
   * @returns {string} 图标
   */
  const getStatusIcon = () => {
    if (result.conditions.is_curtailed) return '⚠️';
    if (!result.need_adjust) return '✅';
    return '🔧';
  };

  /**
   * 格式化功率值，保留1位小数
   * @param {number} value - 功率值
   * @returns {string} 格式化后的字符串
   */
  const formatPower = (value) => {
    if (value === null || value === undefined) return '-';
    return value.toFixed(1);
  };

  /**
   * 获取功率值的样式类
   * @param {number} value - 功率值
   * @returns {string} 样式类名
   */
  const getPowerClass = (value) => {
    if (value > 0) return 'data-item__value data-item__value--positive';
    if (value < 0) return 'data-item__value data-item__value--negative';
    return 'data-item__value';
  };

  const statusType = getStatusType();

  /**
   * 渲染决策依据表
   */
  const renderDecisionTable = () => {
    const { conditions, target_power, deviation, dispatch_target, need_adjust } = result;
    
    // 计算一些额外的判断状态
    const isCharging = result.storage_power < 0;
    const isDischarging = result.storage_power > 0;
    const isAtLimit = !conditions.in_limit;
    
    const rows = [
      { label: '限电状态', value: conditions.is_curtailed ? '🔴 发生限电' : '🟢 正常', type: conditions.is_curtailed ? 'danger' : 'on' },
      { label: '死区判断', value: conditions.in_dead_zone ? '🟢 死区内' : '🔵 死区外', type: conditions.in_dead_zone ? 'on' : 'off' },
      { label: '充放状态', value: isDischarging ? '🔋 放电中' : (isCharging ? '🔌 充电中' : '⚪ 闲置'), type: isDischarging ? 'on' : (isCharging ? 'warn' : 'off') },
      { label: '电量限值', value: isAtLimit ? '🚨 达到限值' : '🟢 正常范围', type: isAtLimit ? 'danger' : 'on' },
      { label: '建议调节', value: need_adjust ? '✅ 立即调节' : '⚪ 保持当前', type: need_adjust ? 'warn' : 'off' }
    ];

    return (
      <table className="decision-table">
        <thead>
          <tr>
            <th>判断维度</th>
            <th>状态/结论</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              <td>{row.label}</td>
              <td>
                <span className={`status-chip status-chip--${row.type}`}>{row.value}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  };

  /**
   * 渲染增强型堆叠图 (支持负值)
   */
  const renderStackedChart = () => {
    const RANGE = 120; // 这里的 100% 对应 +/- 120MW
    
    const getPos = (val) => {
      const percent = (val / (RANGE * 2)) * 100 + 50;
      return `${Math.min(100, Math.max(0, percent))}%`;
    };

    const getWidth = (val) => {
      const width = (Math.abs(val) / (RANGE * 2)) * 100;
      return `${width}%`;
    };

    const { pv_power, storage_power, total_power, dispatch_target } = result;

    return (
      <div className="stacked-bar-container">
        <div style={{ marginBottom: '1.5rem' }}>
          <div className="stacked-bar-label">
            <span>📊 功率分布对比 (光伏 + 储能)</span>
            <span>合: {formatPower(total_power)} MW</span>
          </div>
          <div className="stacked-bar-axis-wrapper">
            <div className="bar-zero-line"></div>
            {/* PV 始终显示在正值区 */}
            <div 
              className="bar-segment bar-segment--pv" 
              style={{ left: getPos(0), width: getWidth(pv_power) }}
            >PV</div>
            
            {/* 储能根据正负显示 */}
            <div 
              className={`bar-segment bar-segment--storage-${storage_power >= 0 ? 'pos' : 'neg'}`}
              style={{ 
                left: storage_power >= 0 ? getPos(pv_power) : getPos(storage_power), 
                width: getWidth(storage_power) 
              }}
            >Bat</div>
          </div>
        </div>

        <div>
          <div className="stacked-bar-label">
            <span>🎯 调度计划线 vs 实际</span>
            <span>计划: {formatPower(dispatch_target)} MW</span>
          </div>
          <div className="stacked-bar-axis-wrapper" style={{ background: 'rgba(255,255,255,0.02)' }}>
            <div className="bar-zero-line"></div>
            {/* 调度目标框 */}
            <div 
              className="bar-segment bar-segment--target"
              style={{ left: getPos(0), width: getWidth(dispatch_target) }}
            >Target</div>
            
            {/* 实际总出力指示点/短轴 */}
            <div 
              style={{ 
                position: 'absolute', 
                left: getPos(total_power), 
                width: '4px', 
                height: '100%', 
                background: 'var(--primary-400)',
                zIndex: 20,
                boxShadow: '0 0 10px var(--primary-400)'
              }}
            ></div>
          </div>
        </div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', color: 'var(--gray-500)', marginTop: '0.5rem' }}>
          <span>充电 (负) ◀</span>
          <span>0 MW</span>
          <span>▶ 放电 (正)</span>
        </div>
      </div>
    );
  };

  return (
    <div className="card animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div className="card__header" style={{ border: 'none', marginBottom: 0 }}>
          <div className="card__icon">📈</div>
          <h2 className="card__title">调节决策中心</h2>
        </div>
        
        {/* SOC 电池柱状图 */}
        <div style={{ textAlign: 'center' }}>
          <div className="battery-pillar">
            <div 
              className="battery-fill" 
              style={{ 
                height: `calc(${result.soc || 0}% - 6px)`,
                background: (result.soc || 0) < 15 ? 'var(--danger-500)' : (result.soc || 0) < 30 ? 'var(--warning-500)' : 'var(--success-500)'
              }}
            />
          </div>
          <div style={{ fontSize: '0.7rem', marginTop: '0.4rem', color: 'var(--gray-400)', fontWeight: 'bold' }}>SOC: {result.soc || '0'}%</div>
        </div>
      </div>
      
      {/* 状态指示 */}
      <div className={`result__status result__status--${statusType}`} style={{ marginTop: '-1rem' }}>
        <div className={`result__indicator result__indicator--${statusType}`}>
          {getStatusIcon()}
        </div>
        <div className="result__message">
          <div className="result__title">{result.adjustment_result}</div>
          <div className="result__subtitle">
            特征码: <span className="feature-code">{result.feature_code}</span>
          </div>
        </div>
      </div>

      {/* 核心数据网格 */}
      <div className="data-grid">
        <div className="data-item">
          <div className="data-item__label">单次调节步长</div>
          <div className="data-item__value">
            {formatPower(result.deviation)} 
            <span className="data-item__unit">MW</span>
          </div>
        </div>
        
        <div className="data-item">
          <div className="data-item__label">本次执行目标</div>
          <div className={getPowerClass(result.target_power)}>
            {result.target_power !== null ? formatPower(result.target_power) : '保持'}
            {result.target_power !== null && <span className="data-item__unit">MW</span>}
          </div>
        </div>

        <div className="data-item">
          <div className="data-item__label">理论理想目标</div>
          <div className="data-item__value" style={{ color: 'var(--gray-400)' }}>
            {formatPower(result.ideal_target_power)}
            <span className="data-item__unit">MW</span>
          </div>
        </div>
      </div>

      {/* 判断依据表 */}
      {renderDecisionTable()}

      {/* 可视化堆叠图 */}
      {renderStackedChart()}

      {/* 实际值对照面板 */}
      {result.actual_comparison && (
        <div className="comparison-box">
          <div className="form-label" style={{ marginBottom: '1rem', justifyContent: 'center' }}>⚖️ 实际响应监测</div>
          <div className="comparison-grid">
            {result.actual_comparison.storage_deviation !== undefined && (
              <div className="comparison-item">
                <span className="form-label__unit" style={{ display: 'block' }}>当前响应偏差</span>
                <span className={`comparison-val ${Math.abs(result.actual_comparison.storage_deviation) > 1 ? 'data-item__value--negative' : 'data-item__value--positive'}`}>
                  {result.actual_comparison.storage_deviation > 0 ? '+' : ''}{result.actual_comparison.storage_deviation.toFixed(2)} MW
                </span>
                <small style={{ color: 'var(--gray-500)' }}>实际出力 vs 计算前</small>
              </div>
            )}
            {result.actual_comparison.target_gap !== undefined && (
              <div className="comparison-item">
                <span className="form-label__unit" style={{ display: 'block' }}>目标未达值</span>
                <span className="comparison-val" style={{ color: 'var(--warning-400)' }}>
                  {Math.abs(result.actual_comparison.target_gap).toFixed(2)} MW
                </span>
                <small style={{ color: 'var(--gray-500)' }}>实际 vs 执行目标</small>
              </div>
            )}
          </div>
        </div>
      )}
      
      {/* 告警信息 */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="warnings">
          <div className="form-label" style={{ marginBottom: '0.5rem' }}>⚠️ 告警信息反馈</div>
          {result.warnings.map((warning, index) => (
            <div 
              key={index} 
              className={`warning-item ${warning.includes('🚨') || warning.includes('必须') ? 'warning-item--danger' : ''}`}
            >
              {warning}
            </div>
          ))}
        </div>
      )}
      
      {/* 计算时间 */}
      <div style={{ marginTop: '1rem', textAlign: 'right', color: 'var(--gray-500)', fontSize: '0.75rem' }}>
        计算时间: {new Date(result.timestamp).toLocaleString('zh-CN')}
      </div>
    </div>
  );
}

export default ResultDisplay;
