<script setup lang="ts">
/**
 * 帮助说明页面
 */
</script>

<template>
  <div class="max-w-3xl mx-auto space-y-8">
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8"
    >
      <h1 class="text-3xl font-bold text-indigo-950 tracking-tight">
        ❓ 帮助说明
      </h1>
      <div
        class="px-4 py-1.5 bg-white/40 rounded-full border border-white/60 shadow-inner"
      >
        <span
          class="text-xs font-bold text-indigo-600 uppercase tracking-widest italic"
          >用户使用手册 v1.0</span
        >
      </div>
    </div>

    <!-- 容器 -->
    <div class="grid md:grid-cols-2 gap-8">
      <!-- 快速开始 -->
      <div class="glass-card flex flex-col">
        <div class="p-6 border-b border-white/20 bg-white/30">
          <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <span
              class="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-sm"
              >1</span
            >
            🚀 核心流程说明
          </h2>
        </div>
        <div class="p-6 flex-1">
          <ol class="space-y-4">
            <li
              v-for="(step, i) in [
                '创建任务：填写标题、描述及基本预期',
                '提交审批：等待主管定级 I/D 系数',
                '执行任务：点击“开始”，系统进入计时',
                '提交验收：完成后上传证据，停止计时',
                '评分入库：主管进行 Q 系数评分并关闭任务',
              ]"
              :key="i"
              class="flex items-start gap-4 group"
            >
              <span
                class="mt-1 w-5 h-5 rounded-full bg-indigo-50 text-indigo-400 text-[10px] font-black flex items-center justify-center border border-indigo-100 group-hover:bg-indigo-600 group-hover:text-white transition-colors"
                >{{ i + 1 }}</span
              >
              <p
                class="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors"
              >
                {{ step }}
              </p>
            </li>
          </ol>
        </div>
      </div>

      <!-- 绩效公式 -->
      <div class="glass-card flex flex-col">
        <div class="p-6 border-b border-white/20 bg-white/30">
          <h2 class="text-lg font-bold text-slate-800 flex items-center gap-2">
            <span
              class="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center text-sm"
              >2</span
            >
            📈 绩效计算公式
          </h2>
        </div>
        <div class="p-6 flex-1 flex flex-col">
          <div
            class="bg-indigo-950 text-indigo-100 rounded-2xl p-6 font-black text-center text-xl shadow-inner mb-6 tracking-tighter"
          >
            S = max(0, (B × I × D) × Q × T − P)
          </div>
          <div class="grid grid-cols-2 gap-x-4 gap-y-3">
            <div
              v-for="item in [
                { l: 'B', n: '基准分', v: '100' },
                { l: 'I', n: '重要性', v: '0.5-1.5' },
                { l: 'D', n: '难度', v: '0.8-1.5' },
                { l: 'Q', n: '质量', v: '0.0-1.2' },
                { l: 'T', n: '时效', v: '0.2-1.0' },
                { l: 'P', n: '罚分', v: '≥ 0' },
              ]"
              :key="item.l"
              class="p-3 bg-white/40 rounded-xl border border-white/60"
            >
              <span class="text-xs font-black text-indigo-600">{{
                item.l
              }}</span>
              <p
                class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1"
              >
                {{ item.n }}
              </p>
              <p class="text-sm font-black text-slate-800">{{ item.v }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 状态说明 -->
      <div class="glass-card md:col-span-2">
        <div class="p-6 border-b border-white/20 bg-white/30">
          <h2 class="text-lg font-bold text-slate-800">📊 任务状态流转图</h2>
        </div>
        <div class="p-6 grid grid-cols-2 md:grid-cols-6 gap-4">
          <div
            v-for="st in [
              { c: 'draft', n: '草稿' },
              { c: 'pending', n: '待审批' },
              { c: 'progress', n: '进行中' },
              { c: 'review', n: '待验收' },
              { c: 'completed', n: '已完成' },
              { c: 'rejected', n: '已驳回' },
            ]"
            :key="st.c"
            class="flex flex-col items-center gap-2 p-4 rounded-3xl bg-white/30 border border-white hover:bg-white/80 transition-colors cursor-default"
          >
            <span :class="['status-badge !px-3 !py-1', 'status-' + st.c]">{{
              st.n
            }}</span>
            <span
              class="text-[10px] font-bold text-slate-400 uppercase tracking-tighter"
              >{{ st.c.replace("_", " ") }}</span
            >
          </div>
        </div>
      </div>

      <!-- 红黄牌 -->
      <div class="glass-card md:col-span-2">
        <div class="p-6 border-b border-white/20 bg-white/30">
          <h2 class="text-lg font-bold text-slate-800">🚨 红黄牌考核细则</h2>
        </div>
        <div class="p-6 grid md:grid-cols-2 gap-6">
          <div
            class="bg-yellow-50/50 border border-yellow-100 rounded-3xl p-6 relative overflow-hidden group"
          >
            <div
              class="absolute -right-4 -top-4 text-6xl opacity-10 group-hover:scale-125 transition-transform"
            >
              🟨
            </div>
            <h3 class="text-xl font-black text-yellow-700 mb-2">
              黄牌 (Yellow Card)
            </h3>
            <p
              class="text-sm font-bold text-yellow-800/60 leading-relaxed uppercase tracking-widest mb-4"
            >
              预警触发条件
            </p>
            <p class="text-sm text-yellow-900/80 font-medium">
              距离截止时间不足
              <span class="font-black">24 小时</span>，且当前进度仍低于
              <span class="font-black">50%</span>。
            </p>
          </div>
          <div
            class="bg-red-50/50 border border-red-100 rounded-3xl p-6 relative overflow-hidden group"
          >
            <div
              class="absolute -right-4 -top-4 text-6xl opacity-10 group-hover:scale-125 transition-transform"
            >
              🟥
            </div>
            <h3 class="text-xl font-black text-red-700 mb-2">
              红牌 (Red Card)
            </h3>
            <p
              class="text-sm font-bold text-red-800/60 leading-relaxed uppercase tracking-widest mb-4"
            >
              惩罚触发条件
            </p>
            <p class="text-sm text-red-900/80 font-medium">
              任务逾期超过
              <span class="font-black">3 天</span
              >，或者实际超期天数达到原计划倍数
              <span class="font-black">≥ 1</span>。
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
