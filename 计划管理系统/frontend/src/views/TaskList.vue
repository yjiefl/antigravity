<script setup lang="ts">
/**
 * 任务列表页面
 *
 * PC 端表格视图，移动端卡片视图
 */
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import api from "../api";

const router = useRouter();

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

onMounted(() => {
  loadTasks();
});
</script>

<template>
  <div class="space-y-6">
    <!-- 页头 -->
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-4"
    >
      <h1 class="text-2xl font-bold text-slate-800">📋 任务管理</h1>
      <button @click="router.push('/tasks/new')" class="btn btn-primary">
        ➕ 新建任务
      </button>
    </div>

    <!-- 过滤器 -->
    <div class="card flex flex-col md:flex-row gap-4">
      <div class="flex-1">
        <input
          v-model="keyword"
          type="text"
          placeholder="搜索任务..."
          class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
        />
      </div>
      <select
        v-model="statusFilter"
        class="px-4 py-2 border border-slate-200 rounded-lg focus:border-indigo-500"
      >
        <option
          v-for="opt in statusOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>
    </div>

    <!-- 加载中 -->
    <div v-if="loading" class="text-center py-12 text-slate-400">加载中...</div>

    <!-- 空状态 -->
    <div v-else-if="filteredTasks.length === 0" class="text-center py-12">
      <p class="text-slate-400 text-lg">暂无任务</p>
      <button
        @click="router.push('/tasks/new')"
        class="mt-4 text-indigo-600 hover:text-indigo-700"
      >
        创建第一个任务 →
      </button>
    </div>

    <!-- PC 端表格 -->
    <div v-else class="card overflow-x-auto hide-mobile">
      <table class="w-full">
        <thead>
          <tr class="border-b border-slate-200">
            <th class="text-left py-3 px-4 text-slate-600 font-medium">
              任务标题
            </th>
            <th class="text-left py-3 px-4 text-slate-600 font-medium">状态</th>
            <th class="text-left py-3 px-4 text-slate-600 font-medium">进度</th>
            <th class="text-left py-3 px-4 text-slate-600 font-medium">
              截止日期
            </th>
            <th class="text-left py-3 px-4 text-slate-600 font-medium">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="task in filteredTasks"
            :key="task.id"
            class="border-b border-slate-100 hover:bg-slate-50 cursor-pointer"
            @click="router.push(`/tasks/${task.id}`)"
          >
            <td class="py-3 px-4">
              <p class="font-medium text-slate-800">{{ task.title }}</p>
            </td>
            <td class="py-3 px-4">
              <span :class="['status-badge', getStatusClass(task.status)]">
                {{ getStatusText(task.status) }}
              </span>
            </td>
            <td class="py-3 px-4">
              <div class="flex items-center gap-2">
                <div class="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-indigo-500 rounded-full"
                    :style="{ width: `${task.progress}%` }"
                  ></div>
                </div>
                <span class="text-sm text-slate-600">{{ task.progress }}%</span>
              </div>
            </td>
            <td class="py-3 px-4 text-slate-600">
              {{ formatDate(task.plan_end) }}
            </td>
            <td class="py-3 px-4">
              <button
                class="text-indigo-600 hover:text-indigo-700"
                @click.stop="router.push(`/tasks/${task.id}`)"
              >
                查看
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 移动端卡片 -->
    <div class="hide-desktop space-y-4 pb-20">
      <div
        v-for="task in filteredTasks"
        :key="task.id"
        @click="router.push(`/tasks/${task.id}`)"
        class="card card-hover"
      >
        <div class="flex items-start justify-between mb-3">
          <h3 class="font-medium text-slate-800">{{ task.title }}</h3>
          <span :class="['status-badge', getStatusClass(task.status)]">
            {{ getStatusText(task.status) }}
          </span>
        </div>
        <div class="flex items-center justify-between text-sm text-slate-500">
          <span>截止: {{ formatDate(task.plan_end) }}</span>
          <span class="font-semibold text-indigo-600"
            >{{ task.progress }}%</span
          >
        </div>
        <div class="mt-3 w-full h-2 bg-slate-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-indigo-500 rounded-full transition-all"
            :style="{ width: `${task.progress}%` }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>
