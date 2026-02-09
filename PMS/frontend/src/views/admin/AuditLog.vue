<script setup lang="ts">
/**
 * 审计日志页面
 */
import { ref, onMounted } from "vue";
import api from "../../api";

const logs = ref<any[]>([]);
const loading = ref(false);

// 筛选条件
const filters = ref({
  module: "",
  action: "",
  username: "",
  startDate: "",
  endDate: "",
});

// 统计信息
const stats = ref<any>(null);

// 模块选项
const moduleOptions = [
  { value: "", label: "全部模块" },
  { value: "auth", label: "认证" },
  { value: "user", label: "用户管理" },
  { value: "task", label: "任务管理" },
  { value: "org", label: "组织架构" },
  { value: "system", label: "系统" },
];

// 操作类型选项
const actionOptions = [
  { value: "", label: "全部操作" },
  { value: "login", label: "登录" },
  { value: "logout", label: "登出" },
  { value: "login_failed", label: "登录失败" },
  { value: "user_create", label: "创建用户" },
  { value: "user_update", label: "更新用户" },
  { value: "user_enable", label: "启用用户" },
  { value: "user_disable", label: "禁用用户" },
  { value: "password_reset", label: "重置密码" },
  { value: "task_create", label: "创建任务" },
  { value: "task_update", label: "更新任务" },
];

// 模块颜色映射
const moduleColors: Record<string, string> = {
  auth: "bg-blue-100 text-blue-700",
  user: "bg-purple-100 text-purple-700",
  task: "bg-green-100 text-green-700",
  org: "bg-orange-100 text-orange-700",
  system: "bg-slate-100 text-slate-700",
};

// 操作类型图标
const actionIcons: Record<string, string> = {
  login: "🔓",
  logout: "🚪",
  login_failed: "⚠️",
  user_create: "➕",
  user_update: "✏️",
  user_enable: "✅",
  user_disable: "🚫",
  password_reset: "🔑",
  task_create: "📝",
  task_update: "📋",
};

async function fetchLogs() {
  loading.value = true;
  try {
    const params: any = { limit: 100 };
    if (filters.value.module) params.module = filters.value.module;
    if (filters.value.action) params.action = filters.value.action;
    if (filters.value.username) params.username = filters.value.username;
    if (filters.value.startDate) params.start_date = filters.value.startDate;
    if (filters.value.endDate) params.end_date = filters.value.endDate;
    
    const res = await api.get("/api/audit", { params });
    logs.value = res.data;
  } catch (e) {
    console.error("加载审计日志失败", e);
  } finally {
    loading.value = false;
  }
}

async function fetchStats() {
  try {
    const res = await api.get("/api/audit/stats", { params: { days: 7 } });
    stats.value = res.data;
  } catch (e) {
    console.error("加载统计失败", e);
  }
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  return d.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function resetFilters() {
  filters.value = {
    module: "",
    action: "",
    username: "",
    startDate: "",
    endDate: "",
  };
  fetchLogs();
}

onMounted(() => {
  fetchLogs();
  fetchStats();
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-slate-800">📋 审计日志</h1>
    </div>

    <!-- 统计卡片 -->
    <div v-if="stats" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
        <div class="text-3xl font-bold text-indigo-600">{{ stats.total }}</div>
        <div class="text-sm text-slate-500">近{{ stats.period_days }}天操作</div>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
        <div class="text-3xl font-bold text-blue-600">{{ stats.by_module?.auth || 0 }}</div>
        <div class="text-sm text-slate-500">认证操作</div>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
        <div class="text-3xl font-bold text-purple-600">{{ stats.by_module?.user || 0 }}</div>
        <div class="text-sm text-slate-500">用户管理</div>
      </div>
      <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
        <div class="text-3xl font-bold text-green-600">{{ stats.by_module?.task || 0 }}</div>
        <div class="text-sm text-slate-500">任务操作</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100">
      <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
        <select v-model="filters.module" class="px-3 py-2 border border-slate-200 rounded-lg">
          <option v-for="opt in moduleOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <select v-model="filters.action" class="px-3 py-2 border border-slate-200 rounded-lg">
          <option v-for="opt in actionOptions" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
        </select>
        <input v-model="filters.username" type="text" placeholder="操作人..." class="px-3 py-2 border border-slate-200 rounded-lg">
        <input v-model="filters.startDate" type="date" class="px-3 py-2 border border-slate-200 rounded-lg">
        <div class="flex gap-2">
          <button @click="fetchLogs" class="btn btn-primary flex-1">查询</button>
          <button @click="resetFilters" class="btn btn-secondary">重置</button>
        </div>
      </div>
    </div>

    <!-- 日志列表 -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      <table class="w-full">
        <thead class="bg-slate-50 border-b border-slate-100">
          <tr>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">时间</th>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">模块</th>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">操作</th>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">操作人</th>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">目标</th>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">描述</th>
            <th class="px-4 py-3 text-left text-sm font-bold text-slate-600">IP</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading">
            <td colspan="7" class="p-8 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="logs.length === 0">
            <td colspan="7" class="p-8 text-center text-slate-400">暂无日志</td>
          </tr>
          <tr v-for="log in logs" :key="log.id" class="hover:bg-slate-50 transition-colors">
            <td class="px-4 py-3 text-sm text-slate-600 whitespace-nowrap">
              {{ formatDate(log.created_at) }}
            </td>
            <td class="px-4 py-3">
              <span class="px-2 py-0.5 rounded text-xs font-bold" :class="moduleColors[log.module] || 'bg-slate-100'">
                {{ log.module }}
              </span>
            </td>
            <td class="px-4 py-3 text-sm">
              <span class="mr-1">{{ actionIcons[log.action] || '📌' }}</span>
              {{ log.action }}
            </td>
            <td class="px-4 py-3 text-sm font-bold text-slate-700">
              {{ log.username }}
            </td>
            <td class="px-4 py-3 text-sm text-slate-600">
              <span v-if="log.target_name">{{ log.target_name }}</span>
              <span v-else class="text-slate-400">-</span>
            </td>
            <td class="px-4 py-3 text-sm text-slate-600 max-w-xs truncate" :title="log.description">
              {{ log.description || '-' }}
            </td>
            <td class="px-4 py-3 text-xs text-slate-400 font-mono">
              {{ log.ip_address || '-' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
