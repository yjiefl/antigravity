<script setup lang="ts">
/**
 * 帮助说明页面
 */
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-8">
    <h1 class="text-2xl font-bold text-slate-800">❓ 帮助说明</h1>

    <!-- 快速开始 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">🚀 快速开始</h2>
      <ol class="list-decimal list-inside space-y-3 text-slate-600">
        <li>在任务列表页面点击"新建任务"创建任务</li>
        <li>填写任务标题、描述、时间等信息后保存</li>
        <li>点击"提交审批"将任务发送给主管</li>
        <li>主管审批通过后，任务进入"进行中"状态</li>
        <li>执行过程中随时更新进展</li>
        <li>完成后提交验收，等待主管评分</li>
      </ol>
    </div>

    <!-- 任务状态 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">📊 任务状态说明</h2>
      <div class="space-y-3">
        <div class="flex items-center gap-3">
          <span class="status-badge status-draft">草稿</span>
          <span class="text-slate-600">任务正在编辑中，仅创建者可见</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="status-badge status-pending">待审批</span>
          <span class="text-slate-600">已提交，等待主管设定 I/D 系数</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="status-badge status-progress">进行中</span>
          <span class="text-slate-600">审批通过，开始执行（计时中）</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="status-badge status-review">待验收</span>
          <span class="text-slate-600">已完成，等待主管评分</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="status-badge status-completed">已完成</span>
          <span class="text-slate-600">验收通过，得分已入库</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="status-badge status-rejected">已驳回</span>
          <span class="text-slate-600">验收不通过，需返工</span>
        </div>
      </div>
    </div>

    <!-- 绩效公式 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">📈 绩效算法</h2>
      <div
        class="bg-slate-50 rounded-lg p-4 font-mono text-center text-lg mb-4"
      >
        S = max(0, (B × I × D) × Q × T − P)
      </div>
      <div class="space-y-2 text-slate-600">
        <p><strong>B</strong> (基准分) = 100</p>
        <p><strong>I</strong> (重要性) = 0.5 ~ 1.5，由主管设定</p>
        <p><strong>D</strong> (难度) = 0.8 ~ 1.5，由主管设定</p>
        <p><strong>Q</strong> (质量) = 0.0 ~ 1.2，验收时评分</p>
        <p><strong>T</strong> (时效) = 0.2 ~ 1.0，系统自动计算</p>
        <p><strong>P</strong> (罚分) = 红牌触发的扣分</p>
      </div>
    </div>

    <!-- 红黄牌 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">🚨 红黄牌规则</h2>
      <div class="space-y-4">
        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <p class="font-medium text-yellow-700">黄牌（预警）</p>
          <p class="text-sm text-yellow-600 mt-1">
            距离截止时间 24 小时内，且进度 &lt; 50%
          </p>
        </div>
        <div class="bg-red-50 border-l-4 border-red-400 p-4">
          <p class="font-medium text-red-700">红牌（考核）</p>
          <p class="text-sm text-red-600 mt-1">逾期超过 3 天，或超期倍数 ≥ 1</p>
        </div>
      </div>
    </div>
  </div>
</template>
