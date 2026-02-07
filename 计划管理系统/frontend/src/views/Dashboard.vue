<script setup lang="ts">
/**
 * 仪表盘页面
 *
 * 展示任务概览、风险预警、快速操作
 */
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import api from "../api";

const router = useRouter();
const authStore = useAuthStore();

// 统计数据
const stats = ref({
  totalTasks: 0,
  inProgress: 0,
  pendingReview: 0,
  overdue: 0,
});

// 风险任务列表
const riskTasks = ref<any[]>([]);

// 我的任务
const myTasks = ref<any[]>([]);

// 加载数据
async function loadData() {
  try {
    // 获取任务列表
    const response = await api.get("/api/tasks", {
      params: { limit: 50 },
    });
    const tasks = response.data;

    // 计算统计
    stats.value.totalTasks = tasks.length;
    stats.value.inProgress = tasks.filter(
      (t: any) => t.status === "in_progress",
    ).length;
    stats.value.pendingReview = tasks.filter(
      (t: any) => t.status === "pending_review",
    ).length;

    // 风险任务（逾期或进度滞后）
    const now = new Date();
    riskTasks.value = tasks
      .filter((t: any) => {
        if (t.status !== "in_progress") return false;
        if (t.plan_end && new Date(t.plan_end) < now) return true;
        return false;
      })
      .slice(0, 5);

    stats.value.overdue = riskTasks.value.length;

    // 我的任务
    myTasks.value = tasks
      .filter((t: any) => t.executor_id === authStore.user?.id)
      .slice(0, 5);
  } catch (e) {
    console.error("加载数据失败", e);
  }
}

// 获取状态样式类
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

// 获取状态文本
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

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="space-y-6">
    <!-- 欢迎语 -->
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-2xl font-bold text-slate-800">
          👋 你好，{{ authStore.user?.realName }}
        </h1>
        <p class="text-slate-500 mt-1">欢迎使用计划管理系统</p>
      </div>
      <button @click="router.push('/tasks/new')" class="btn btn-primary">
        ➕ 新建任务
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="card">
        <p class="text-slate-500 text-sm">总任务数</p>
        <p class="text-3xl font-bold text-slate-800 mt-2">
          {{ stats.totalTasks }}
        </p>
      </div>
      <div class="card">
        <p class="text-slate-500 text-sm">进行中</p>
        <p class="text-3xl font-bold text-blue-600 mt-2">
          {{ stats.inProgress }}
        </p>
      </div>
      <div class="card">
        <p class="text-slate-500 text-sm">待验收</p>
        <p class="text-3xl font-bold text-purple-600 mt-2">
          {{ stats.pendingReview }}
        </p>
      </div>
      <div class="card">
        <p class="text-slate-500 text-sm">风险预警</p>
        <p class="text-3xl font-bold text-red-500 mt-2">{{ stats.overdue }}</p>
      </div>
    </div>

    <div class="grid md:grid-cols-2 gap-6">
      <!-- 风险任务 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">🚨 风险预警</h2>
        <div
          v-if="riskTasks.length === 0"
          class="text-slate-400 text-center py-8"
        >
          暂无风险任务
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="task in riskTasks"
            :key="task.id"
            @click="router.push(`/tasks/${task.id}`)"
            class="flex items-center gap-3 p-3 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 transition-colors"
          >
            <span class="text-red-500">⚠️</span>
            <div class="flex-1 min-w-0">
              <p class="font-medium text-slate-800 truncate">
                {{ task.title }}
              </p>
              <p class="text-sm text-red-500">已逾期</p>
            </div>
            <span class="text-sm text-slate-500">{{ task.progress }}%</span>
          </div>
        </div>
      </div>

      <!-- 我的任务 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">📋 我的任务</h2>
        <div
          v-if="myTasks.length === 0"
          class="text-slate-400 text-center py-8"
        >
          暂无任务
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="task in myTasks"
            :key="task.id"
            @click="router.push(`/tasks/${task.id}`)"
            class="flex items-center gap-3 p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
          >
            <div class="flex-1 min-w-0">
              <p class="font-medium text-slate-800 truncate">
                {{ task.title }}
              </p>
              <span :class="['status-badge', getStatusClass(task.status)]">
                {{ getStatusText(task.status) }}
              </span>
            </div>
            <div class="text-right">
              <p class="text-lg font-semibold text-indigo-600">
                {{ task.progress }}%
              </p>
            </div>
          </div>
        </div>
        <button
          @click="router.push('/tasks')"
          class="w-full mt-4 text-center text-indigo-600 hover:text-indigo-700 text-sm"
        >
          查看全部 →
        </button>
      </div>
    </div>
  </div>
</template>
