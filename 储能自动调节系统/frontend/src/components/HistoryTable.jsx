/**
 * 储能自动调节系统 - 历史记录表格组件
 * 
 * 展示调节计算的历史记录
 */

import React from 'react';

/**
 * 历史记录表格组件
 * 
 * @param {Object} props - 组件属性
 * @param {Array} props.history - 历史记录数组
 * @param {Function} props.onClear - 清空历史记录处理函数
 * @param {boolean} props.loading - 是否正在加载
 */
function HistoryTable({ history, onClear, loading }) {
  
  /**
   * 格式化时间戳
   * @param {string} timestamp - ISO时间戳
   * @returns {string} 格式化后的时间字符串
   */
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  /**
   * 格式化功率值
   * @param {number} value - 功率值
   * @returns {string} 格式化后的字符串
   */
  const formatPower = (value) => {
    if (value === null || value === undefined) return '-';
    return value.toFixed(1);
  };

  if (loading) {
    return (
      <div className="card history">
        <div className="card__header">
          <div className="card__icon">📋</div>
          <h2 className="card__title">历史记录</h2>
        </div>
        <div className="loading">
          <span className="loading__spinner"></span>
          加载中...
        </div>
      </div>
    );
  }

  return (
    <div className="card history">
      <div className="card__header">
        <div className="card__icon">📋</div>
        <h2 className="card__title">历史记录</h2>
        {history.length > 0 && (
          <button 
            className="btn btn--secondary" 
            onClick={onClear}
            style={{ marginLeft: 'auto' }}
          >
            🗑️ 清空
          </button>
        )}
      </div>
      
      {history.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state__icon">📝</div>
          <div className="empty-state__title">暂无记录</div>
          <div className="empty-state__description">计算结果将自动保存到这里</div>
        </div>
      ) : (
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>时间</th>
                <th>调度指令</th>
                <th>SOC</th>
                <th>理论目标</th>
                <th>执行目标</th>
                <th>实际偏差</th>
                <th>调节结果</th>
              </tr>
            </thead>
            <tbody>
              {history.map((record, index) => {
                const deviation = record.actual_storage_power !== null ? 
                  (record.actual_storage_power - (record.target_power || record.storage_power)) : null;
                
                return (
                  <tr key={record.id || index} className="animate-fade-in">
                    <td style={{ whiteSpace: 'nowrap' }}>{formatTime(record.timestamp)}</td>
                    <td>{formatPower(record.dispatch_target)} MW</td>
                    <td>{record.soc?.toFixed(1)}%</td>
                    <td style={{ color: 'var(--gray-400)' }}>{formatPower(record.ideal_target_power)}</td>
                    <td style={{ fontWeight: 'bold' }}>{formatPower(record.target_power)}</td>
                    <td style={{ 
                      color: deviation === null ? 'var(--gray-600)' : 
                             Math.abs(deviation) > 1.0 ? 'var(--danger-400)' : 'var(--success-400)'
                    }}>
                      {deviation !== null ? `${deviation > 0 ? '+' : ''}${formatPower(deviation)}` : '-'}
                    </td>
                    <td style={{ maxWidth: '200px' }}>
                      <div className="feature-code" style={{ display: 'inline-block', marginRight: '8px' }}>{record.feature_code}</div>
                      <span style={{ fontSize: '0.8rem' }}>{record.adjustment_result}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default HistoryTable;
