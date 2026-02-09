<script setup lang="ts">
/**
 * 任务列表页面
 *
 * PC 端表格视图，移动端卡片视图
 */
import { ref, onMounted, computed, watch } from "vue";
import { useRouter, useRoute } from "vue-router";
import api from "../api";

const router = useRouter();
const route = useRoute();

// 任务列表
const tasks = ref<any[]>([]);
const loading = ref(true);

// 过滤条件
const statusFilter = ref("");
const keyword = ref("");

// 过滤后的任务
const filteredTasks = computed(() => {
  let result = tasks.value;

  if (statusFilter.value) {
    result = result.filter((t) => t.status === statusFilter.value);
  }

  if (keyword.value) {
    const kw = keyword.value.toLowerCase();
    result = result.filter(
      (t) =>
        t.title.toLowerCase().includes(kw) ||
        t.description?.toLowerCase().includes(kw),
    );
  }

  return result;
});

// 状态选项
const statusOptions = [
  { value: "", label: "全部状态" },
  { value: "draft", label: "草稿" },
  { value: "pending_approval", label: "待审批" },
  { value: "in_progress", label: "进行中" },
  { value: "pending_review", label: "待验收" },
  { value: "completed", label: "已完成" },
  { value: "rejected", label: "已驳回" },
];

// 加载任务
async function loadTasks() {
  loading.value = true;
  try {
    const response = await api.get("/api/tasks", {
      params: { limit: 100 },
    });
    tasks.value = response.data;
  } catch (e) {
    console.error("加载任务失败", e);
  } finally {
    loading.value = false;
  }
}

// 状态样式
function getStatusClass(status: string) {
  const map: Record<string, string> = {
    draft: "status-draft",
    pending_approval: "status-pending",
    in_progress: "status-progress",
    pending_review: "status-review",
    completed: "status-completed",
    rejected: "status-rejected",
  };
  return map[status] || "status-draft";
}

// 状态文本
function getStatusText(status: string) {
  const map: Record<string, string> = {
    draft: "草稿",
    pending_approval: "待审批",
    in_progress: "进行中",
    pending_review: "待验收",
    completed: "已完成",
    rejected: "已驳回",
  };
  return map[status] || status;
}

// 格式化日期
function formatDate(dateStr: string) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("zh-CN");
}

// 导出报表
async function handleExport() {
  try {
    const response = await api.get("/api/reports/export/tasks", {
      params: {
        status: statusFilter.value || undefined,
        // keyword filters are client-side only based on current implementation?
        // Backend has keyword param?
        // list_tasks has keyword. reports.py didn't include keyword param?
        // Let's check reports.py content again.
        // reports.py: status_filter, task_type, executor_id, owner_id, start_date, end_date.
        // NO KEYWORD.
        // So export might not filter by keyword.
        // I'll skip keyword for now or accept it if I update backend.
        // For now, just status.
      },
      responseType: "blob",
    });

    // 获取文件名 (从 header 中解析，或者自动生成)
    const filename = `task_report_${new Date().toISOString().slice(0, 10)}.xlsx`;

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (e) {
    console.error("导出失败", e);
    alert("导出失败，请重试");
  }
}

// 读取 URL query 参数初始化过滤状态
function initFromQuery() {
  const queryStatus = route.query.status as string;
  if (queryStatus && statusOptions.some(opt => opt.value === queryStatus)) {
    statusFilter.value = queryStatus;
  }
}

// 监听路由变化 (从仪表盘点击进入时)
watch(() => route.query.status, (newStatus) => {
  if (newStatus && typeof newStatus === 'string') {
    statusFilter.value = newStatus;
  }
});

onMounted(() => {
  initFromQuery();
  loadTasks();
});
</script>

<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-6"
    >
      <div>
        <h1 class="text-3xl font-bold text-indigo-950 tracking-tight">
          📋 任务管理
        </h1>
        <p class="text-slate-500 mt-1 font-medium">
          查看并管理您的所有计划任务
        </p>
      </div>
      <div class="flex gap-3">
        <button
          @click="handleExport"
          class="btn btn-secondary border-indigo-200"
        >
          📊 导出报表
        </button>
        <button
          @click="router.push('/tasks/new')"
          class="btn btn-primary shadow-indigo-100"
        >
          ➕ 新建任务
        </button>
      </div>
    </div>

    <!-- 过滤器 -->
    <div class="glass-card p-4 flex flex-col md:flex-row gap-4">
      <div class="flex-1 relative group">
        <span
          class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors"
          >🔍</span
        >
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索任务标题或描述..."
          class="w-full pl-11 pr-4 py-2.5 bg-white/50 border border-slate-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all outline-none"
        />
      </div>
      <div class="relative">
        <select
          v-model="statusFilter"
          class="w-full md:w-48 appearance-none pl-4 pr-10 py-2.5 bg-white/50 border border-slate-200 rounded-xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all outline-none cursor-pointer font-semibold text-slate-700"
        >
          <option
            v-for="opt in statusOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
        <span
          class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400"
          >▼</span
        >
      </div>
    </div>

    <!-- 加载中 -->
    <div
      v-if="loading"
      class="flex flex-col items-center justify-center py-24 gap-4"
    >
      <div
        class="w-12 h-12 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"
      ></div>
      <p class="text-indigo-900/40 font-bold uppercase tracking-widest text-sm">
        加载任务中...
      </p>
    </div>

    <!-- 空状态 -->
    <div
      v-else-if="filteredTasks.length === 0"
      class="glass-card py-20 flex flex-col items-center text-center"
    >
      <div
        class="w-20 h-20 bg-indigo-50 rounded-3xl flex items-center justify-center text-3xl mb-6"
      >
        🏜️
      </div>
      <h3 class="text-xl font-bold text-slate-800">暂无任务</h3>
      <p class="text-slate-500 mt-2">没有找到符合当前过滤条件的任务</p>
      <button @click="router.push('/tasks/new')" class="mt-6 btn btn-primary">
        创建第一个任务
      </button>
    </div>

    <!-- PC 端表格 -->
    <div v-else class="glass-card overflow-hidden hide-mobile">
      <table class="w-full border-collapse">
        <thead>
          <tr class="bg-indigo-50/50">
            <th
              class="text-left py-4 px-6 text-indigo-900/60 font-bold uppercase tracking-widest text-[10px]"
            >
              任务信息
            </th>
            <th
              class="text-left py-4 px-6 text-indigo-900/60 font-bold uppercase tracking-widest text-[10px]"
            >
              状态
            </th>
            <th
              class="text-center py-4 px-3 text-indigo-900/60 font-bold uppercase tracking-widest text-[10px]"
              title="重要性/难度系数"
            >
              I/D
            </th>
            <th
              class="text-left py-4 px-6 text-indigo-900/60 font-bold uppercase tracking-widest text-[10px]"
            >
              进度
            </th>
            <th
              class="text-left py-4 px-6 text-indigo-900/60 font-bold uppercase tracking-widest text-[10px]"
            >
              截止日期
            </th>
            <th
              class="text-right py-4 px-6 text-indigo-900/60 font-bold uppercase tracking-widest text-[10px]"
            >
              操作
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-white/20">
          <tr
            v-for="task in filteredTasks"
            :key="task.id"
            class="group hover:bg-white/40 cursor-pointer transition-all duration-200"
            @click="router.push(`/tasks/${task.id}`)"
          >
            <td class="py-4 px-6">
              <p
                class="font-bold text-slate-800 group-hover:text-indigo-600 transition-colors"
              >
                {{ task.title }}
              </p>
              <p class="text-xs text-slate-400 mt-0.5">
                {{ task.description || "无描述" }}
              </p>
            </td>
            <td class="py-4 px-6">
              <span :class="['status-badge', getStatusClass(task.status)]">
                {{ getStatusText(task.status) }}
              </span>
            </td>
            <td class="py-4 px-3 text-center">
              <div v-if="task.importance_i || task.difficulty_d" class="flex flex-col items-center gap-0.5">
                <span class="text-xs font-bold text-amber-600" :title="'重要性: ' + (task.importance_i || '-')">
                  I:{{ task.importance_i?.toFixed(1) || '-' }}
                </span>
                <span class="text-xs font-bold text-blue-600" :title="'难度: ' + (task.difficulty_d || '-')">
                  D:{{ task.difficulty_d?.toFixed(1) || '-' }}
                </span>
              </div>
              <span v-else class="text-xs text-slate-300">-</span>
            </td>
            <td class="py-4 px-6">
              <div class="flex items-center gap-3">
                <div class="w-32 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-indigo-500 rounded-full transition-all duration-500"
                    :style="{ width: `${task.progress}%` }"
                  ></div>
                </div>
                <span class="text-xs font-black text-slate-600 tabular-nums"
                  >{{ task.progress }}%</span
                >
              </div>
            </td>
            <td class="py-4 px-6">
              <div class="flex flex-col">
                <span class="text-sm font-semibold text-slate-700">{{
                  formatDate(task.plan_end)
                }}</span>
                <span
                  v-if="task.plan_end && new Date(task.plan_end) < new Date()"
                  class="text-[10px] text-red-500 font-bold uppercase tracking-tighter"
                  >已过期</span
                >
              </div>
            </td>
            <td class="py-4 px-6 text-right">
              <button
                class="btn btn-secondary py-1 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                @click.stop="router.push(`/tasks/${task.id}`)"
              >
                查看详情
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 移动端卡片 -->
    <div class="hide-desktop space-y-4 pb-24">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        @click="router.push(`/tasks/${task.id}`)"
        class="glass-card p-5 active:scale-95 transition-transform"
      >
        <div class="flex items-start justify-between mb-4">
          <div class="flex-1 min-w-0">
            <h3
              class="font-bold text-slate-800 text-lg leading-tight truncate px-1"
            >
              {{ task.title }}
            </h3>
            <span :class="['status-badge mt-2', getStatusClass(task.status)]">
              {{ getStatusText(task.status) }}
            </span>
          </div>
          <div
            class="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center text-xl shadow-inner"
          >
            {{ task.status === "completed" ? "✅" : "📝" }}
          </div>
        </div>

        <div
          class="flex items-center justify-between text-xs font-bold uppercase tracking-widest text-slate-400 mb-2"
        >
          <span>📅 {{ formatDate(task.plan_end) }}</span>
          <span class="text-indigo-600">{{ task.progress }}%</span>
        </div>

        <div class="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-indigo-500 rounded-full transition-all duration-500"
            :style="{ width: `${task.progress}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
