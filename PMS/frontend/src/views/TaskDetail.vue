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

// 模态框控制
const showProgressModal = ref(false);
const showHistoryModal = ref(false);
const showCompleteModal = ref(false);
const showReviewModal = ref(false);
const showApproveModal = ref(false);
// const showPreviewModal = ref(false);
// const previewUrl = ref("");

// 表单数据
const progressForm = ref({ percent: 0, content: "", files: [] as File[] });
const completeForm = ref({ comment: "", files: [] as File[] });
const reviewForm = ref({ quality: 1.0, comment: "" });
const approveForm = ref({ importance: 1.0, difficulty: 1.0 });

function handleProgressFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    // Append instead of replace to support "one by one" upload experience if requested
    // But system currently replaces. Let's stick to simple multiple for now.
    progressForm.value.files = Array.from(target.files);
  }
}

function handleCompleteFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    completeForm.value.files = Array.from(target.files);
  }
}

// function openPreview(url: string) {
//   previewUrl.value = url;
//   showPreviewModal.value = true;
// }

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

    // 初始化表单
    progressForm.value.percent = task.value.progress;
  } catch (e) {
    console.error("加载任务失败", e);
  } finally {
    loading.value = false;
  }
}

// 进度历史（从日志筛选）
const progressHistory = computed(() => {
  return logs.value
    .filter((l) => l.progress_after !== null)
    .sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
    );
});

// 状态操作
async function submitTask() {
  if (!confirm("确认提交审批？提交后无法修改关键信息。")) return;
  await api.post(`/api/tasks/${taskId.value}/submit`);
  await loadTask();
}

async function rollbackTask() {
  if (!confirm("确认回撤申请？任务将返回进行中状态。")) return;
  await api.post(`/api/tasks/${taskId.value}/rollback`);
  await loadTask();
}

async function approveTask() {
  await api.post(`/api/tasks/${taskId.value}/approve`, {
    importance_i: approveForm.value.importance,
    difficulty_d: approveForm.value.difficulty,
  });
  showApproveModal.value = false;
  await loadTask();
}

async function updateProgress() {
  if (!progressForm.value.content) {
    alert("请输入进展说明");
    return;
  }

  if (progressForm.value.percent < task.value.progress) {
    if (
      !confirm(
        `新进度 (${progressForm.value.percent}%) 低于当前进度 (${task.value.progress}%)，将被记录为进度回退且可能影响绩效得分。确认提交吗？`,
      )
    ) {
      return;
    }
  }

  const formData = new FormData();
  formData.append("progress", progressForm.value.percent.toString());
  formData.append("content", progressForm.value.content);
  if (progressForm.value.files.length > 0) {
    progressForm.value.files.forEach((f) => {
      formData.append("files", f);
    });
  }

  await api.post(`/api/tasks/${taskId.value}/progress`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  showProgressModal.value = false;
  progressForm.value.content = "";
  progressForm.value.files = [];
  await loadTask();
}

async function completeTask() {
  // Ensure task is at 100% (either current or in the progress modal if it was open)
  if (task.value.progress < 100 && progressForm.value.percent < 100) {
    alert("必须先将进度更新至 100% 才能提交验收");
    return;
  }

  const formData = new FormData();
  if (completeForm.value.comment) {
    formData.append("comment", completeForm.value.comment);
  }
  if (completeForm.value.files.length > 0) {
    completeForm.value.files.forEach((f) => {
      formData.append("files", f);
    });
  }

  await api.post(`/api/tasks/${taskId.value}/complete`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  showCompleteModal.value = false;
  completeForm.value.comment = "";
  completeForm.value.files = [];
  await loadTask();
}

// 格式化文件大小
function formatFileSize(bytes: number) {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

async function reviewTask() {
  await api.post(`/api/tasks/${taskId.value}/review`, {
    quality_q: reviewForm.value.quality,
    comment: reviewForm.value.comment || null,
  });
  showReviewModal.value = false;
  await loadTask();
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
    suspended: "已挂起",
    cancelled: "已取消",
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
    system_notice: "系统通知",
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
    <div class="card relative overflow-hidden">
      <!-- 顶部装饰条 -->
      <div
        class="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"
      ></div>

      <div class="flex items-start justify-between mb-4 mt-2">
        <div>
          <h1 class="text-2xl font-bold text-slate-800">{{ task.title }}</h1>
          <div class="flex items-center gap-2 mt-1 text-sm text-slate-500">
            <span class="px-2 py-0.5 bg-slate-100 rounded text-xs">{{
              task.category
            }}</span>
            <span>{{
              task.task_type === "performance" ? "绩效任务" : "日常任务"
            }}</span>
            <span>•</span>
            <span
              >{{ new Date(task.created_at).toLocaleDateString() }} 创建</span
            >
          </div>
        </div>
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

      <p class="text-slate-600 mb-6 whitespace-pre-wrap">
        {{ task.description || "暂无描述" }}
      </p>

      <!-- 进度条 -->
      <div class="mb-6 bg-slate-50 p-4 rounded-xl border border-slate-100">
        <div class="flex justify-between text-sm mb-2">
          <div class="flex items-center gap-2">
            <span class="text-slate-600 font-medium">完成进度</span>
            <button
              @click="showHistoryModal = true"
              class="text-xs text-indigo-600 hover:text-indigo-800 underline"
            >
              查看历史
            </button>
          </div>
          <span class="font-bold text-indigo-600 text-lg"
            >{{ task.progress }}%</span
          >
        </div>
        <div
          class="w-full h-4 bg-slate-200 rounded-full overflow-hidden shadow-inner"
        >
          <div
            class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-500 ease-out relative"
            :style="{ width: `${task.progress}%` }"
          >
            <div class="absolute inset-0 bg-white/20 animate-pulse"></div>
          </div>
        </div>
      </div>

      <!-- 系数信息 -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div
          class="bg-indigo-50/50 border border-indigo-100 rounded-lg p-3 text-center"
        >
          <p class="text-xs text-indigo-500 font-bold uppercase tracking-wider">
            重要性 I
          </p>
          <p class="text-xl font-black text-indigo-900 mt-1">
            {{ task.importance_i || "1.0" }}
          </p>
        </div>
        <div
          class="bg-purple-50/50 border border-purple-100 rounded-lg p-3 text-center"
        >
          <p class="text-xs text-purple-500 font-bold uppercase tracking-wider">
            难度 D
          </p>
          <p class="text-xl font-black text-purple-900 mt-1">
            {{ task.difficulty_d || "1.0" }}
          </p>
        </div>
        <div
          class="bg-pink-50/50 border border-pink-100 rounded-lg p-3 text-center"
        >
          <p class="text-xs text-pink-500 font-bold uppercase tracking-wider">
            质量 Q
          </p>
          <p class="text-xl font-black text-pink-900 mt-1">
            {{ task.quality_q || "-" }}
          </p>
        </div>
        <div
          class="bg-amber-50/50 border border-amber-100 rounded-lg p-3 text-center relative overflow-hidden"
        >
          <div
            class="absolute -right-4 -top-4 w-12 h-12 bg-amber-200 rounded-full blur-xl opacity-50"
          ></div>
          <p class="text-xs text-amber-600 font-bold uppercase tracking-wider">
            最终得分
          </p>
          <p class="text-xl font-black text-amber-700 mt-1">
            {{ task.final_score?.toFixed(1) || "-" }}
          </p>
        </div>
      </div>

      <!-- 得分预览 -->
      <div
        v-if="scorePreview && task.status === 'in_progress'"
        class="bg-gradient-to-br from-slate-800 to-slate-900 text-white rounded-xl p-5 mb-6 shadow-lg shadow-slate-200 relative overflow-hidden"
      >
        <div
          class="absolute right-0 top-0 w-32 h-32 bg-indigo-500 rounded-full blur-3xl opacity-20 transform translate-x-10 -translate-y-10"
        ></div>
        <div class="relative z-10 flex justify-between items-center">
          <div>
            <p
              class="text-slate-400 text-xs font-bold uppercase tracking-widest mb-1"
            >
              当前预计得分
            </p>
            <div class="text-3xl font-black">
              {{ scorePreview.current_score.toFixed(1) }}
              <span class="text-base font-normal text-slate-400"
                >/ {{ scorePreview.max_possible_score.toFixed(1) }}</span
              >
            </div>
          </div>
          <div v-if="scorePreview.is_overdue" class="text-right">
            <div
              class="px-3 py-1 bg-red-500/20 border border-red-500/50 text-red-300 rounded-lg text-sm font-bold flex items-center gap-2"
            >
              <span>⚠️ 已逾期 {{ scorePreview.overdue_days }} 天</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="flex flex-wrap gap-3 pt-4 border-t border-slate-100">
        <!-- 草稿 -> 提交审批 -->
        <button
          v-if="task.status === 'draft'"
          @click="submitTask"
          class="btn btn-primary"
        >
          提交审批
        </button>

        <button
          v-if="task.status === 'draft'"
          @click="router.push(`/tasks/new?id=${task.id}`)"
          class="btn btn-secondary"
        >
          编辑任务
        </button>

        <!-- 待审批 -> 审批通过 (Manager) -->
        <button
          v-if="task.status === 'pending_approval' && authStore.isManager"
          @click="showApproveModal = true"
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
          @click="showCompleteModal = true"
          class="btn btn-primary"
        >
          提交验收
        </button>

        <!-- 待验收 -> 验收评分 (Manager) -->
        <button
          v-if="task.status === 'pending_review' && authStore.isManager"
          @click="showReviewModal = true"
          class="btn btn-primary"
        >
          验收评分
        </button>

        <!-- 待验收 -> 回撤 (Creator/Executor) -->
        <button
          v-if="task.status === 'pending_review'"
          @click="rollbackTask"
          class="btn btn-secondary"
        >
          ↩️ 回撤申请
        </button>
      </div>
    </div>

    <!-- 日志 -->
    <div class="card">
      <h2
        class="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2"
      >
        <span>📝</span> 任务日志
      </h2>
      <div v-if="logs.length === 0" class="text-slate-400 text-center py-4">
        暂无日志
      </div>
      <div
        v-else
        class="space-y-0 relative border-l-2 border-slate-100 ml-4 pl-6 pb-2"
      >
        <div v-for="log in logs" :key="log.id" class="relative mb-8 last:mb-0">
          <!-- 时间轴点 -->
          <div
            class="absolute -left-[31px] top-1 w-4 h-4 rounded-full border-2 border-white box-content"
            :class="
              log.action.includes('error') || log.action === 'rejected'
                ? 'bg-red-500'
                : 'bg-indigo-500'
            "
          ></div>

          <div class="flex justify-between items-start">
            <div>
              <p class="font-bold text-slate-700">
                {{ getActionText(log.action) }}
              </p>
              <p
                v-if="log.content"
                class="text-sm text-slate-600 mt-1 bg-slate-50 p-2 rounded-lg inline-block"
              >
                {{ log.content }}
              </p>
              <div
                v-if="log.attachments && log.attachments.length > 0"
                class="mt-3 space-y-2"
              >
                <div
                  v-for="att in log.attachments"
                  :key="att.id"
                  class="flex items-center gap-3 p-2 bg-white/50 border border-slate-100 rounded-lg group hover:bg-white transition-all"
                >
                  <!-- 图片预览 -->
                  <template v-if="att.file_type.startsWith('image/')">
                    <a :href="att.file_path" target="_blank" class="shrink-0">
                      <img
                        :src="att.file_path"
                        class="h-12 w-12 object-cover rounded border border-slate-100 hover:scale-110 transition-transform"
                      />
                    </a>
                  </template>
                  <template v-else>
                    <span class="text-2xl shrink-0">📄</span>
                  </template>

                  <div class="flex-1 min-w-0">
                    <p
                      class="text-xs font-medium text-slate-700 truncate"
                      :title="att.filename"
                    >
                      {{ att.filename }}
                    </p>
                    <p class="text-[10px] text-slate-400">
                      {{ formatFileSize(att.file_size) }} •
                      {{ new Date(att.created_at).toLocaleString() }} • 下载
                      {{ att.download_count }} 次
                    </p>
                  </div>

                  <a
                    :href="`/api/attachments/${att.id}/download?token=${authStore.token}`"
                    target="_blank"
                    class="btn btn-secondary !py-1 !px-2 !text-[10px] opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    📥 下载
                  </a>
                </div>
              </div>
              <div v-else-if="log.evidence_url" class="mt-2 text-xs">
                <div
                  v-if="log.evidence_url.match(/\.(jpg|jpeg|png|gif)$/i)"
                  class="mt-1"
                >
                  <a :href="log.evidence_url" target="_blank">
                    <img
                      :src="log.evidence_url"
                      class="h-20 rounded border border-slate-200 hover:scale-110 transition-transform cursor-zoom-in"
                      alt="证据截图"
                    />
                  </a>
                </div>
                <a
                  v-else
                  :href="log.evidence_url"
                  target="_blank"
                  class="text-blue-500 hover:underline flex items-center gap-1"
                >
                  📎 查看附件/证据
                </a>
              </div>
            </div>
            <span class="text-xs text-slate-400">
              {{ new Date(log.created_at).toLocaleString("zh-CN") }}
            </span>
          </div>

          <div
            v-if="log.progress_after !== null"
            class="text-xs font-bold text-indigo-600 mt-1 flex items-center gap-1"
          >
            <span>🚀 进度更新:</span>
            <span class="text-slate-400 line-through"
              >{{ log.progress_before }}%</span
            >
            <span>→</span>
            <span>{{ log.progress_after }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 模态框组 -->

    <!-- 1. 审批模态框 -->
    <div
      v-if="showApproveModal"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    >
      <div
        class="bg-white rounded-xl shadow-2xl w-full max-w-sm overflow-hidden animate-fade-in-up"
      >
        <div
          class="p-4 border-b border-slate-100 bg-slate-50 flex justify-between items-center"
        >
          <h3 class="font-bold text-slate-800">✅ 审批定级</h3>
          <button
            @click="showApproveModal = false"
            class="text-slate-400 hover:text-slate-600"
          >
            ✕
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-bold text-slate-700 mb-1"
              >重要性系数 (I)</label
            >
            <input
              type="number"
              step="0.1"
              min="0.5"
              max="1.5"
              v-model.number="approveForm.importance"
              class="w-full input"
            />
            <p class="text-xs text-slate-400 mt-1">范围: 0.5 - 1.5</p>
          </div>
          <div>
            <label class="block text-sm font-bold text-slate-700 mb-1"
              >难度系数 (D)</label
            >
            <input
              type="number"
              step="0.1"
              min="0.8"
              max="1.5"
              v-model.number="approveForm.difficulty"
              class="w-full input"
            />
            <p class="text-xs text-slate-400 mt-1">范围: 0.8 - 1.5</p>
          </div>
          <button @click="approveTask" class="btn btn-primary w-full mt-2">
            确认通过
          </button>
        </div>
      </div>
    </div>

    <!-- 2. 更新进展模态框 -->
    <div
      v-if="showProgressModal"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    >
      <div
        class="bg-white rounded-xl w-full max-w-md overflow-hidden animate-fade-in-up"
      >
        <div class="p-4 border-b border-slate-100 bg-slate-50">
          <h3 class="font-bold text-slate-800">📈 更新进展</h3>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label
              class="block text-sm font-bold text-slate-700 mb-2 flex justify-between"
            >
              <span>当前进度</span>
              <span class="text-indigo-600">{{ progressForm.percent }}%</span>
            </label>
            <input
              type="range"
              v-model.number="progressForm.percent"
              min="0"
              max="100"
              class="w-full accent-indigo-600 h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
            />
            <p
              v-if="progressForm.percent < task.progress"
              class="text-xs text-amber-600 mt-2 font-bold flex items-center gap-1"
            >
              ⚠️ 如果新进度低于当前进度 ({{
                task.progress
              }}%)，将被视为进度回退。
            </p>
          </div>

          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2"
              >进展说明</label
            >
            <textarea
              v-model="progressForm.content"
              rows="3"
              class="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-100 outline-none"
              placeholder="描述本次完成了什么..."
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2"
              >附件/截图 (可多选)</label
            >
            <div class="relative group">
              <input
                type="file"
                @change="handleProgressFileChange"
                class="hidden"
                id="progress-file"
                multiple
              />
              <label
                for="progress-file"
                class="flex items-center gap-2 w-full px-3 py-2 border border-slate-200 border-dashed rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
              >
                <span class="text-xl">📎</span>
                <span class="text-sm text-slate-500 truncate">
                  {{
                    progressForm.files.length > 0
                      ? `已选择 ${progressForm.files.length} 个文件`
                      : "点击上传文件..."
                  }}
                </span>
              </label>
            </div>
            <div v-if="progressForm.files.length > 0" class="mt-2 space-y-1">
              <div
                v-for="f in progressForm.files"
                :key="f.name"
                class="text-[10px] text-slate-500 flex justify-between"
              >
                <span>{{ f.name }}</span>
                <span>{{ formatFileSize(f.size) }}</span>
              </div>
            </div>
          </div>

          <div class="flex gap-3 mt-2">
            <button
              @click="showProgressModal = false"
              class="btn btn-secondary flex-1"
            >
              取消
            </button>
            <button @click="updateProgress" class="btn btn-primary flex-1">
              提交更新
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 3. 提交验收模态框 -->
    <div
      v-if="showCompleteModal"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    >
      <div
        class="bg-white rounded-xl w-full max-w-md overflow-hidden animate-fade-in-up"
      >
        <div class="p-4 border-b border-slate-100 bg-green-50">
          <h3 class="font-bold text-green-800">🎉 提交验收</h3>
        </div>
        <div class="p-6 space-y-4">
          <div class="bg-yellow-50 p-3 rounded-lg text-xs text-yellow-700 mb-2">
            ⚠️ 提交验收前请确保任务已 100% 完成。
          </div>
          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2"
              >交付物/证据 (可多选) *</label
            >
            <div class="relative group">
              <input
                type="file"
                @change="handleCompleteFileChange"
                class="hidden"
                id="complete-file"
                multiple
              />
              <label
                for="complete-file"
                class="flex items-center gap-2 w-full px-3 py-2 border border-slate-200 border-dashed rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
              >
                <span class="text-xl">📦</span>
                <span class="text-sm text-slate-500 truncate">
                  {{
                    completeForm.files.length > 0
                      ? `已选择 ${completeForm.files.length} 个文件`
                      : "点击上传交付物 (必须)..."
                  }}
                </span>
              </label>
            </div>
            <div v-if="completeForm.files.length > 0" class="mt-2 space-y-1">
              <div
                v-for="f in completeForm.files"
                :key="f.name"
                class="text-[10px] text-slate-500 flex justify-between"
              >
                <span>{{ f.name }}</span>
                <span>{{ formatFileSize(f.size) }}</span>
              </div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2"
              >完成备注</label
            >
            <textarea
              v-model="completeForm.comment"
              rows="3"
              class="w-full px-3 py-2 border rounded-lg"
              placeholder="如果有特别说明..."
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              @click="showCompleteModal = false"
              class="btn btn-secondary flex-1"
            >
              取消
            </button>
            <button @click="completeTask" class="btn btn-primary flex-1">
              确认提交
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 4. 验收评分模态框 -->
    <div
      v-if="showReviewModal"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
    >
      <div
        class="bg-white rounded-xl w-full max-w-sm overflow-hidden animate-fade-in-up"
      >
        <div class="p-4 border-b border-slate-100 bg-slate-50">
          <h3 class="font-bold text-slate-800">⚖️ 验收评分</h3>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2"
              >质量系数 (Q)</label
            >
            <div class="flex items-center gap-4">
              <input
                type="number"
                step="0.1"
                min="0"
                max="1.2"
                v-model.number="reviewForm.quality"
                class="w-20 px-3 py-2 border rounded-lg font-bold text-center"
              />
              <input
                type="range"
                class="flex-1 accent-indigo-600"
                min="0"
                max="1.2"
                step="0.1"
                v-model.number="reviewForm.quality"
              />
            </div>
            <p class="text-xs text-slate-400 mt-1">
              范围: 0.0 - 1.2 (1.0 为合格)
            </p>
          </div>
          <div>
            <label class="block text-sm font-bold text-slate-700 mb-2"
              >评语</label
            >
            <textarea
              v-model="reviewForm.comment"
              rows="3"
              class="w-full px-3 py-2 border rounded-lg"
              placeholder="做得好，但是..."
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              @click="showReviewModal = false"
              class="btn btn-secondary flex-1"
            >
              取消
            </button>
            <button @click="reviewTask" class="btn btn-primary flex-1">
              提交结果
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 5. 历史记录模态框 -->
    <div
      v-if="showHistoryModal"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click.self="showHistoryModal = false"
    >
      <div
        class="bg-white rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col overflow-hidden animate-fade-in-up"
      >
        <div
          class="p-4 border-b border-slate-100 flex justify-between items-center"
        >
          <h3 class="font-bold text-slate-800">📅 进度变更历史</h3>
          <button
            @click="showHistoryModal = false"
            class="text-slate-400 hover:text-slate-600"
          >
            ✕
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-0">
          <table class="w-full text-sm text-left">
            <thead class="bg-slate-50 text-slate-500 font-medium">
              <tr>
                <th class="p-3">时间</th>
                <th class="p-3">变更</th>
                <th class="p-3">说明</th>
                <th class="p-3">附件</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr
                v-for="h in progressHistory"
                :key="h.id"
                class="hover:bg-slate-50/50"
              >
                <td class="p-3 text-slate-500">
                  {{ new Date(h.created_at).toLocaleString() }}
                </td>
                <td class="p-3">
                  <span class="font-bold text-indigo-600"
                    >{{ h.progress_after }}%</span
                  >
                  <span class="text-xs text-slate-400 ml-1"
                    >(从 {{ h.progress_before }}%)</span
                  >
                </td>
                <td class="p-3 text-slate-700">{{ h.content || "-" }}</td>
                <td class="p-3">
                  <div
                    v-if="h.attachments && h.attachments.length > 0"
                    class="flex flex-wrap gap-2"
                  >
                    <a
                      v-for="att in h.attachments"
                      :key="att.id"
                      :href="`/api/attachments/${att.id}/download?token=${authStore.token}`"
                      target="_blank"
                      class="text-blue-500 hover:underline flex items-center gap-1 text-[10px]"
                      :title="att.filename"
                    >
                      <span>{{
                        att.file_type.startsWith("image/") ? "📷" : "📎"
                      }}</span>
                      <span class="max-w-[80px] truncate">{{
                        att.filename
                      }}</span>
                    </a>
                  </div>
                  <a
                    v-else-if="h.evidence_url"
                    :href="h.evidence_url"
                    target="_blank"
                    class="text-blue-500 hover:underline flex items-center gap-1"
                  >
                    <span v-if="h.evidence_url.match(/\.(jpg|jpeg|png|gif)$/i)"
                      >📷 图片</span
                    >
                    <span v-else>📎 文件</span>
                  </a>
                  <span v-else class="text-slate-300">-</span>
                </td>
              </tr>
              <tr v-if="progressHistory.length === 0">
                <td colspan="4" class="p-8 text-center text-slate-400">
                  暂无进度变更记录
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>
