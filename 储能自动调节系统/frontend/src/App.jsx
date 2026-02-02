/**
 * 储能自动调节系统 - 主应用组件
 * 
 * 光储电站储能AGC有功控制系统
 */

import React, { useState, useEffect, useCallback } from 'react';
import InputForm from './components/InputForm';
import ResultDisplay from './components/ResultDisplay';
import HistoryTable from './components/HistoryTable';

// API基础URL
const API_BASE = '/api/v1';

/**
 * 主应用组件
 */
function App() {
  // 表单数据状态
  const [formData, setFormData] = useState({
    storage_power: -12.0,      // 储能当前出力（MW）
    dispatch_target: 63.0,     // 调度指令值（MW）
    pv_power: 73.0,            // 光伏出力（MW）
    charge_limit: -50.0,       // 储能充电上限（MW）
    discharge_limit: 50.0,     // 储能放电上限（MW）
    dead_zone: 1.2,            // 死区值（MW）
    soc: 50.0,                 // 当前SOC（%）
    soc_min: 8.0,              // SOC下限（%）
    actual_storage_power: 0,   // 储能实际值
    actual_pv_power: 0,        // 光伏实际值
    step_size: 2.0             // 步长
  });

  // 倒计时状态
  const [countdown, setCountdown] = useState(0);

  // 计算结果状态
  const [result, setResult] = useState(null);
  
  // 历史记录状态
  const [history, setHistory] = useState([]);
  
  // 加载状态
  const [loading, setLoading] = useState(false);
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // 错误状态
  const [error, setError] = useState(null);

  /**
   * 获取历史记录
   */
  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`${API_BASE}/history?limit=20`);
      if (response.ok) {
        const data = await response.json();
        setHistory(data);
      }
    } catch (err) {
      console.error('获取历史记录失败:', err);
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  // 组件挂载时获取历史记录
  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  /**
   * 执行调节计算
   */
  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${API_BASE}/calculate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '计算失败');
      }
      
      const data = await response.json();
      setResult(data);
      
      // 设置倒计时
      if (data.next_adjust_delay) {
        setCountdown(data.next_adjust_delay);
      }
      
      // 刷新历史记录
      fetchHistory();
      
    } catch (err) {
      setError(err.message);
      console.error('计算失败:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 倒计时效果
   */
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  /**
   * 清空历史记录
   */
  const handleClearHistory = async () => {
    if (!confirm('确定要清空所有历史记录吗？')) {
      return;
    }
    
    try {
      const response = await fetch(`${API_BASE}/history`, {
        method: 'DELETE'
      });
      
      if (response.ok) {
        setHistory([]);
      }
    } catch (err) {
      console.error('清空历史记录失败:', err);
    }
  };

  return (
    <div className="app">
      {/* 头部 */}
      <header className="header">
        <h1 className="header__title">⚡ 储能自动调节系统</h1>
        <p className="header__subtitle">光储电站储能AGC有功控制 · 智能调节策略计算</p>
      </header>
      
      {/* 倒计时提示 */}
      {countdown > 0 && (
        <div className="warning-item" style={{ marginBottom: '1.5rem', background: 'rgba(59, 130, 246, 0.1)', borderColor: 'rgba(59, 130, 246, 0.3)', color: 'var(--primary-300)' }}>
          ⏱️ 建议下一次调节在 {countdown} 秒后进行
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="warning-item warning-item--danger" style={{ marginBottom: '1.5rem' }}>
          ❌ 错误: {error}
        </div>
      )}
      
      {/* 主要内容区域 */}
      <main className="main-grid">
        {/* 左侧：输入表单 */}
        <InputForm 
          formData={formData}
          onFormChange={setFormData}
          onSubmit={handleCalculate}
          loading={loading}
        />
        
        {/* 右侧：结果展示 */}
        <ResultDisplay result={result} />
      </main>
      
      {/* 历史记录 */}
      <HistoryTable 
        history={history}
        onClear={handleClearHistory}
        loading={historyLoading}
      />
      
      {/* 页脚 */}
      <footer style={{ 
        marginTop: '2rem', 
        textAlign: 'center', 
        color: 'var(--gray-500)',
        fontSize: '0.875rem',
        paddingTop: '1.5rem',
        borderTop: '1px solid var(--gray-800)'
      }}>
        <p>储能自动调节系统 v1.0.0 · 基于AGC有功控制逻辑</p>
        <p style={{ marginTop: '0.5rem', fontSize: '0.75rem' }}>
          光伏P + 储能P = 调度指令值
        </p>
      </footer>
    </div>
  );
}

export default App;
