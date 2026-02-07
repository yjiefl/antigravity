<script setup lang="ts">
/**
 * 任务详情页面
 */
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import api from "../api";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const taskId = computed(() => route.params.id as string);
const task = ref<any>(null);
const logs = ref<any[]>([]);
const loading = ref(true);
const scorePreview = ref<any>(null);

// 进展更新
const progressInput = ref(0);
const progressContent = ref("");
const showProgressModal = ref(false);

// 加载任务
async function loadTask() {
  loading.value = true;
  try {
    const [taskRes, logsRes, scoreRes] = await Promise.all([
      api.get(`/api/tasks/${taskId.value}`),
      api.get(`/api/tasks/${taskId.value}/logs`),
      api.get(`/api/kpi/preview/${taskId.value}`),
    ]);
    task.value = taskRes.data;
    logs.value = logsRes.data;
    scorePreview.value = scoreRes.data;
    progressInput.value = task.value.progress;
  } catch (e) {
    console.error("加载任务失败", e);
  } finally {
    loading.value = false;
  }
}

// 状态操作
async function submitTask() {
  await api.post(`/api/tasks/${taskId.value}/submit`);
  await loadTask();
}

async function approveTask() {
  const i = prompt("请输入重要性系数 I (0.5-1.5):", "1.0");
  const d = prompt("请输入难度系数 D (0.8-1.5):", "1.0");
  if (i && d) {
    await api.post(`/api/tasks/${taskId.value}/approve`, {
      importance_i: parseFloat(i),
      difficulty_d: parseFloat(d),
    });
    await loadTask();
  }
}

async function updateProgress() {
  await api.post(`/api/tasks/${taskId.value}/progress`, {
    progress: progressInput.value,
    content: progressContent.value,
  });
  showProgressModal.value = false;
  progressContent.value = "";
  await loadTask();
}

async function completeTask() {
  const evidence = prompt("请输入验收证据链接（可选）:");
  await api.post(`/api/tasks/${taskId.value}/complete`, {
    evidence_url: evidence || null,
  });
  await loadTask();
}

async function reviewTask() {
  const q = prompt("请输入质量系数 Q (0.0-1.2):", "1.0");
  if (q) {
    await api.post(`/api/tasks/${taskId.value}/review`, {
      quality_q: parseFloat(q),
    });
    await loadTask();
  }
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

// 操作文本
function getActionText(action: string) {
  const map: Record<string, string> = {
    created: "创建任务",
    submitted: "提交审批",
    approved: "审批通过",
    rejected: "审批驳回",
    progress_updated: "更新进展",
    completed: "提交验收",
    reviewed: "验收评分",
  };
  return map[action] || action;
}

onMounted(() => {
  loadTask();
});
</script>

<template>
  <div v-if="loading" class="text-center py-12 text-slate-400">加载中...</div>

  <div v-else-if="task" class="space-y-6 pb-20 md:pb-6">
    <!-- 返回按钮 -->
    <button
      @click="router.push('/tasks')"
      class="text-slate-500 hover:text-slate-700"
    >
      ← 返回列表
    </button>

    <!-- 任务信息卡片 -->
    <div class="card">
      <div class="flex items-start justify-between mb-4">
        <h1 class="text-2xl font-bold text-slate-800">{{ task.title }}</h1>
        <span
          class="status-badge"
          :class="{
            'status-draft': task.status === 'draft',
            'status-pending': task.status === 'pending_approval',
            'status-progress': task.status === 'in_progress',
            'status-review': task.status === 'pending_review',
            'status-completed': task.status === 'completed',
            'status-rejected': task.status === 'rejected',
          }"
        >
          {{ getStatusText(task.status) }}
        </span>
      </div>

      <p class="text-slate-600 mb-6">{{ task.description || "暂无描述" }}</p>

      <!-- 进度条 -->
      <div class="mb-6">
        <div class="flex justify-between text-sm mb-2">
          <span class="text-slate-600">完成进度</span>
          <span class="font-semibold text-indigo-600"
            >{{ task.progress }}%</span
          >
        </div>
        <div class="w-full h-3 bg-slate-200 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all"
            :style="{ width: `${task.progress}%` }"
          ></div>
        </div>
      </div>

      <!-- 系数信息 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-slate-50 rounded-lg p-3 text-center">
          <p class="text-xs text-slate-500">重要性 I</p>
          <p class="text-lg font-semibold text-slate-800">
            {{ task.importance_i || "-" }}
          </p>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 text-center">
          <p class="text-xs text-slate-500">难度 D</p>
          <p class="text-lg font-semibold text-slate-800">
            {{ task.difficulty_d || "-" }}
          </p>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 text-center">
          <p class="text-xs text-slate-500">质量 Q</p>
          <p class="text-lg font-semibold text-slate-800">
            {{ task.quality_q || "-" }}
          </p>
        </div>
        <div class="bg-slate-50 rounded-lg p-3 text-center">
          <p class="text-xs text-slate-500">得分</p>
          <p class="text-lg font-semibold text-indigo-600">
            {{ task.final_score?.toFixed(1) || "-" }}
          </p>
        </div>
      </div>

      <!-- 得分预览 -->
      <div
        v-if="scorePreview && task.status === 'in_progress'"
        class="bg-indigo-50 rounded-lg p-4 mb-6"
      >
        <p class="text-sm text-indigo-700">
          📊 当前预计得分:
          <strong>{{ scorePreview.current_score.toFixed(1) }}</strong>
          <span v-if="scorePreview.is_overdue" class="text-red-500 ml-2">
            (已逾期 {{ scorePreview.overdue_days }} 天)
          </span>
        </p>
      </div>

      <!-- 操作按钮 -->
      <div class="flex flex-wrap gap-3">
        <!-- 草稿 -> 提交审批 -->
        <button
          v-if="task.status === 'draft'"
          @click="submitTask"
          class="btn btn-primary"
        >
          提交审批
        </button>

        <!-- 待审批 -> 审批通过 (Manager) -->
        <button
          v-if="task.status === 'pending_approval' && authStore.isManager"
          @click="approveTask"
          class="btn btn-primary"
        >
          审批通过
        </button>

        <!-- 进行中 -> 更新进展 -->
        <button
          v-if="task.status === 'in_progress'"
          @click="showProgressModal = true"
          class="btn btn-secondary"
        >
          更新进展
        </button>

        <!-- 进行中 -> 提交验收 -->
        <button
          v-if="task.status === 'in_progress'"
          @click="completeTask"
          class="btn btn-primary"
        >
          提交验收
        </button>

        <!-- 待验收 -> 验收评分 (Manager) -->
        <button
          v-if="task.status === 'pending_review' && authStore.isManager"
          @click="reviewTask"
          class="btn btn-primary"
        >
          验收评分
        </button>
      </div>
    </div>

    <!-- 日志 -->
    <div class="card">
      <h2 class="text-lg font-semibold text-slate-800 mb-4">📝 任务日志</h2>
      <div v-if="logs.length === 0" class="text-slate-400 text-center py-4">
        暂无日志
      </div>
      <div v-else class="space-y-4">
        <div
          v-for="log in logs"
          :key="log.id"
          class="flex gap-4 p-3 bg-slate-50 rounded-lg"
        >
          <div
            class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 shrink-0"
          >
            📌
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-medium text-slate-800">
              {{ getActionText(log.action) }}
            </p>
            <p v-if="log.content" class="text-sm text-slate-600 mt-1">
              {{ log.content }}
            </p>
            <p
              v-if="log.progress_after !== null"
              class="text-sm text-slate-500 mt-1"
            >
              进度: {{ log.progress_before }}% → {{ log.progress_after }}%
            </p>
            <p class="text-xs text-slate-400 mt-1">
              {{ new Date(log.created_at).toLocaleString("zh-CN") }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- 进展更新弹窗 -->
    <div
      v-if="showProgressModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
      @click.self="showProgressModal = false"
    >
      <div class="bg-white rounded-xl p-6 w-full max-w-md">
        <h3 class="text-lg font-semibold text-slate-800 mb-4">更新进展</h3>

        <div class="mb-4">
          <label class="block text-sm text-slate-600 mb-2"
            >进度 ({{ progressInput }}%)</label
          >
          <input
            type="range"
            v-model.number="progressInput"
            min="0"
            max="100"
            class="w-full"
          />
        </div>

        <div class="mb-6">
          <label class="block text-sm text-slate-600 mb-2">进展说明</label>
          <textarea
            v-model="progressContent"
            rows="3"
            class="w-full px-3 py-2 border border-slate-200 rounded-lg"
            placeholder="描述本次进展..."
          ></textarea>
        </div>

        <div class="flex gap-3">
          <button
            @click="showProgressModal = false"
            class="btn btn-secondary flex-1"
          >
            取消
          </button>
          <button @click="updateProgress" class="btn btn-primary flex-1">
            提交
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
