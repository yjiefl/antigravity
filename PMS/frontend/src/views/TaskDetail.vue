<script setup lang="ts">
/**
 * 任务详情页面 - 增强健壮版
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
const showReturnModal = ref(false);
const showPreviewModal = ref(false);
const showExtensionModal = ref(false);
const showCoefficientModal = ref(false);
const previewUrl = ref("");

// 表单数据
const progressForm = ref({ percent: 0, content: "", files: [] as File[] });
const completeForm = ref({ comment: "", files: [] as File[] });
const reviewForm = ref({ quality: 1.0, comment: "" });
const approveForm = ref({ importance: 1.0, difficulty: 1.0 });
const returnForm = ref({ reason: "" });
const extensionForm = ref({ date: "", reason: "" });
const coefficientForm = ref({ importance: 1.0, difficulty: 1.0, reason: "" });

function handleProgressFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    const newFiles = Array.from(target.files);
    progressForm.value.files = [...progressForm.value.files, ...newFiles];
    target.value = "";
  }
}

function handleCompleteFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  if (target.files) {
    const newFiles = Array.from(target.files);
    completeForm.value.files = [...completeForm.value.files, ...newFiles];
    target.value = "";
  }
}

function openPreview(url: string) {
  previewUrl.value = url;
  showPreviewModal.value = true;
}

// 加载任务
async function loadTask() {
  console.log("Loading task details:", taskId.value);
  loading.value = true;
  try {
    const [taskRes, logsRes, scoreRes] = await Promise.all([
      api.get(`/api/tasks/${taskId.value}`).catch(e => { console.error("Task API Error:", e); throw e; }),
      api.get(`/api/tasks/${taskId.value}/logs`).catch(e => { console.error("Logs API Error:", e); return { data: [] }; }),
      api.get(`/api/kpi/preview/${taskId.value}`).catch(e => { console.error("Score API Error:", e); return { data: null }; }),
    ]);
    
    task.value = taskRes.data;
    logs.value = logsRes.data;
    scorePreview.value = scoreRes.data;

    if (task.value) {
      progressForm.value.percent = task.value.progress || 0;
    }
    console.log("Task loaded successfully");
  } catch (e) {
    console.error("加载任务失败", e);
    task.value = null;
  } finally {
    loading.value = false;
  }
}

// 进度历史
const progressHistory = computed(() => {
  if (!logs.value) return [];
  return logs.value
    .filter((l) => l && l.progress_after !== null && l.progress_after !== undefined)
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
  if (!confirm("确认回撤验收申请？任务将返回进行中状态。")) return;
  await api.post(`/api/tasks/${taskId.value}/rollback`);
  await loadTask();
}

async function withdrawTask() {
  if (!confirm("确认撤回审批申请？任务将返回草稿状态。")) return;
  await api.post(`/api/tasks/${taskId.value}/withdraw`);
  await loadTask();
}

async function returnTask() {
  if (!returnForm.value.reason) {
    alert("请输入退回原因");
    return;
  }
  await api.post(
    `/api/tasks/${taskId.value}/return?reason=${encodeURIComponent(returnForm.value.reason)}`,
  );
  showReturnModal.value = false;
  returnForm.value.reason = "";
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

async function approveTaskLeader() {
  if (!confirm("确认通过该任务？将提交给主管审批。")) return;
  await api.post(`/api/tasks/${taskId.value}/approve-leader`);
  await loadTask();
}

function canAdjustCoefficients() {
  if (!task.value) return false;
  if (task.value.status === 'draft') return false;
  return authStore.isAdmin || authStore.isManager;
}

function openCoefficientModal() {
  if (!task.value) return;
  coefficientForm.value.importance = task.value.importance_i || 1.0;
  coefficientForm.value.difficulty = task.value.difficulty_d || 1.0;
  coefficientForm.value.reason = "";
  showCoefficientModal.value = true;
}

async function updateCoefficients() {
  if (!coefficientForm.value.reason) {
     alert("请输入调整原因");
     return;
  }
  await api.put(`/api/tasks/${taskId.value}/coefficients`, {
     importance_i: coefficientForm.value.importance,
     difficulty_d: coefficientForm.value.difficulty,
     reason: coefficientForm.value.reason
  });
  showCoefficientModal.value = false;
  await loadTask();
}

async function approveExtension() {
  if (!confirm("确认通过延期申请？")) return;
  await api.post(`/api/tasks/${taskId.value}/approve-extension`);
  await loadTask();
}

async function rejectExtension() {
  if (!confirm("确认驳回延期申请？")) return;
  await api.post(`/api/tasks/${taskId.value}/reject-extension`);
  await loadTask();
}

async function updateProgress() {
  if (!progressForm.value.content) {
    alert("请输入进展说明");
    return;
  }
  if (progressForm.value.percent < task.value.progress) {
    if (!confirm(`新进度 (${progressForm.value.percent}%) 低于当前进度 (${task.value.progress}%)，将被记录为进度回退。确认提交吗？`)) {
      return;
    }
  }
  const formData = new FormData();
  formData.append("progress", progressForm.value.percent.toString());
  formData.append("content", progressForm.value.content);
  progressForm.value.files.forEach((f: File) => {
    formData.append("files", f);
  });
  await api.post(`/api/tasks/${taskId.value}/progress`, formData);
  showProgressModal.value = false;
  progressForm.value.content = "";
  progressForm.value.files = [];
  await loadTask();
}

async function completeTask() {
  if (task.value.progress < 100 && progressForm.value.percent < 100) {
    alert("必须先将进度更新至 100% 才能提交验收");
    return;
  }
  const formData = new FormData();
  if (completeForm.value.comment) {
    formData.append("comment", completeForm.value.comment);
  }
  completeForm.value.files.forEach((f: File) => {
    formData.append("files", f);
  });
  await api.post(`/api/tasks/${taskId.value}/complete`, formData);
  showCompleteModal.value = false;
  completeForm.value.comment = "";
  completeForm.value.files = [];
  await loadTask();
}

function formatFileSize(bytes: number) {
  if (!bytes || bytes === 0) return "0 B";
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

async function requestExtension() {
  if (!extensionForm.value.date || !extensionForm.value.reason) {
    alert("请填写完整的延期日期和理由");
    return;
  }
  await api.post(`/api/tasks/${taskId.value}/request-extension`, {
    extension_date: extensionForm.value.date,
    extension_reason: extensionForm.value.reason,
  });
  showExtensionModal.value = false;
  await loadTask();
}

function canReview(): boolean {
  if (!task.value || !authStore.user) return false;
  if (authStore.isAdmin) return true;
  if (!authStore.isManager) return false;
  if (task.value.reviewer_id) return task.value.reviewer_id === authStore.user.id;
  return true;
}

function canCreateSubtask(): boolean {
  if (!task.value || !authStore.user) return false;
  if (['draft', 'pending_submission', 'in_progress'].includes(task.value.status)) {
     return task.value.creator_id === authStore.user.id || 
            task.value.owner_id === authStore.user.id ||
            authStore.isAdmin;
  }
  return false;
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    draft: "草稿",
    pending_submission: "待提交",
    pending_leader_approval: "待组长审批",
    pending_approval: "待主管审批",
    in_progress: "进行中",
    pending_review: "待验收",
    completed: "已完成",
    rejected: "已驳回",
    suspended: "已挂起",
    cancelled: "已取消",
  };
  return map[status] || status;
}

function getActionText(action: string) {
  const map: Record<string, string> = {
    created: "创建任务",
    submitted: "提交审批",
    leader_approved: "组长通过",
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
  <div v-if="loading" class="text-center py-12 text-slate-400">
    <div class="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent mb-4"></div>
    <p>加载中...</p>
  </div>

  <div v-else-if="!task" class="text-center py-20 bg-white rounded-2xl shadow-xl border border-slate-100 mx-4 animate-fade-in">
    <div class="text-6xl mb-4">🔍</div>
    <h3 class="text-xl font-bold text-slate-800 mb-2">未找到该任务</h3>
    <p class="text-slate-500 mb-6">任务可能已被删除或您没有查看权限</p>
    <button @click="router.push('/tasks')" class="btn btn-primary px-8">返回任务列表</button>
  </div>

  <div v-else class="space-y-6 pb-20 md:pb-6 animate-fade-in">
    <!-- 返回按钮 -->
    <button @click="router.push('/tasks')" class="text-slate-500 hover:text-indigo-600 flex items-center gap-1 transition-colors font-medium">
      <span class="text-xl">←</span> 返回列表
    </button>

    <!-- 任务信息卡片 -->
    <div class="card relative overflow-hidden group">
      <div class="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
      
      <div class="flex flex-col md:flex-row md:items-start justify-between gap-4 mb-6 mt-2">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-2xl font-black text-slate-800 tracking-tight">{{ task.title }}</h1>
            <span class="px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded text-[10px] uppercase font-black">{{ task.category }}</span>
          </div>
          <div class="flex flex-wrap items-center gap-3 text-sm text-slate-500 font-medium">
            <span class="flex items-center gap-1">📋 {{ task.task_type === "performance" ? "绩效任务" : "日常任务" }}</span>
            <span class="text-slate-300">•</span>
            <span class="flex items-center gap-1">🕒 {{ task.created_at ? new Date(task.created_at).toLocaleDateString() : '-' }} 创建</span>
            <span v-if="task.owner_name" class="text-slate-300">•</span>
            <span v-if="task.owner_name" class="flex items-center gap-1">👤 负责人: {{ task.owner_name }}</span>
          </div>
        </div>
        <div class="flex items-center gap-2 self-start">
          <span class="status-badge px-4 py-1.5 rounded-full text-xs font-black shadow-sm uppercase tracking-wider" :class="'status-' + task.status">
            {{ getStatusText(task.status) }}
          </span>
        </div>
      </div>

      <div class="bg-slate-50/80 backdrop-blur-sm rounded-2xl p-5 border border-slate-100 mb-6 group-hover:border-indigo-100 transition-colors">
        <h4 class="text-xs font-black text-slate-400 uppercase tracking-widest mb-2 flex items-center gap-2">
          <span>📄</span> 任务描述
        </h4>
        <p class="text-slate-600 leading-relaxed whitespace-pre-wrap">{{ task.description || "暂无描述" }}</p>
      </div>

      <!-- 进度条 -->
      <div class="mb-8 bg-slate-50/50 p-6 rounded-2xl border border-slate-100 shadow-inner">
        <div class="flex justify-between items-end mb-3">
          <div class="flex items-center gap-3">
            <div class="p-2 bg-indigo-100 text-indigo-600 rounded-lg">
              <span class="text-lg">📈</span>
            </div>
            <div>
              <p class="text-xs font-black text-slate-400 uppercase tracking-widest">当前进度</p>
              <button @click="showHistoryModal = true" class="text-xs text-indigo-600 hover:text-indigo-800 font-bold underline underline-offset-4">查看历史记录</button>
            </div>
          </div>
          <span class="font-black text-indigo-600 text-3xl tabular-nums">{{ task.progress }}<span class="text-lg ml-0.5">%</span></span>
        </div>
        <div class="w-full h-4 bg-slate-200 rounded-full overflow-hidden shadow-inner p-0.5">
          <div class="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full transition-all duration-1000 ease-out relative shadow-lg" :style="{ width: `${task.progress}%` }">
            <div class="absolute inset-0 bg-white/20 animate-pulse"></div>
          </div>
        </div>
      </div>

      <!-- 系数信息 & 指标 -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <div v-if="task.workload_b > 0" class="glass-stat p-4 rounded-2xl border border-blue-100 text-center">
          <p class="stat-label text-blue-500">工作量 B</p>
          <p class="stat-value text-blue-900">{{ task.workload_b }}</p>
        </div>
        <div class="glass-stat p-4 rounded-2xl border border-indigo-100 text-center">
          <p class="stat-label text-indigo-500">重要性 I</p>
          <p class="stat-value text-indigo-900">{{ task.importance_i || "1.0" }}</p>
        </div>
        <div class="glass-stat p-4 rounded-2xl border border-purple-100 text-center">
          <p class="stat-label text-purple-500">难度 D</p>
          <p class="stat-value text-purple-900">{{ task.difficulty_d || "1.0" }}</p>
        </div>
        <div class="glass-stat p-4 rounded-2xl border border-pink-100 text-center">
          <p class="stat-label text-pink-500">质量 Q</p>
          <p class="stat-value text-pink-900">{{ task.quality_q || "-" }}</p>
        </div>
        <div class="glass-stat p-4 rounded-2xl border border-teal-100 text-center">
          <p class="stat-label text-teal-500">时效 T</p>
          <p class="stat-value text-teal-900">{{ task.timeliness_t || "-" }}</p>
        </div>
        <div class="glass-stat bg-gradient-to-br from-amber-50 to-orange-50 p-4 rounded-2xl border border-amber-100 text-center relative overflow-hidden">
          <div class="absolute -right-4 -top-4 w-12 h-12 bg-amber-200 rounded-full blur-2xl opacity-40"></div>
          <p class="stat-label text-amber-600">最终得分</p>
          <p class="stat-value text-amber-800">{{ task.final_score?.toFixed(1) || "-" }}</p>
        </div>
      </div>

      <!-- 得分预览 -->
      <div v-if="scorePreview && task.status === 'in_progress'" class="bg-slate-900 text-white rounded-2xl p-6 mb-8 shadow-2xl relative overflow-hidden ring-1 ring-white/10">
        <div class="absolute right-0 top-0 w-64 h-64 bg-indigo-600/20 rounded-full blur-[80px]"></div>
        <div class="relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
          <div class="flex items-center gap-4">
            <div class="p-3 bg-white/10 rounded-xl backdrop-blur-md">
              <span class="text-2xl">💎</span>
            </div>
            <div>
              <p class="text-slate-400 text-xs font-black uppercase tracking-[0.2em] mb-1">当前预计得分预览</p>
              <div class="text-4xl font-black tabular-nums">
                {{ scorePreview.current_score.toFixed(1) }}
                <span class="text-lg font-medium text-slate-500 ml-1">/ {{ scorePreview.max_possible_score.toFixed(1) }}</span>
              </div>
            </div>
          </div>
          <div v-if="scorePreview.is_overdue" class="text-right">
            <div class="px-4 py-2 bg-red-500/20 border border-red-500/30 text-red-300 rounded-xl text-sm font-black flex items-center gap-2 backdrop-blur-md">
              <span class="animate-pulse">⚠️</span> 已逾期 {{ scorePreview.overdue_days }} 天
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按钮区域 -->
      <div class="flex flex-wrap gap-4 pt-6 border-t border-slate-100">
        <!-- 主按钮组 -->
        <template v-if="task.status === 'draft'">
          <button @click="submitTask" class="btn btn-primary px-8">提交审批</button>
          <button @click="router.push(`/tasks/new?id=${task.id}`)" class="btn bg-slate-100 text-slate-700 hover:bg-slate-200">编辑任务</button>
        </template>

        <template v-if="task.status === 'pending_submission'">
          <button @click="submitTask" class="btn btn-primary px-8">提交审批</button>
          <button @click="router.push(`/tasks/new?id=${task.id}`)" class="btn bg-slate-100 text-slate-700 hover:bg-slate-200">编辑任务</button>
          <button @click="withdrawTask" class="btn text-slate-400 hover:text-red-500 hover:bg-red-50 ml-auto">取消任务</button>
        </template>
        
        <template v-if="task.status === 'pending_leader_approval' && canReview()">
          <button @click="approveTaskLeader" class="btn btn-primary px-8">组长通过</button>
          <button @click="showReturnModal = true" class="btn btn-danger">驳回/退回</button>
        </template>

        <template v-if="task.status === 'pending_approval' && canReview()">
          <button @click="showApproveModal = true" class="btn btn-primary px-8">审批通过/定级</button>
          <button @click="showReturnModal = true" class="btn btn-danger">退回修改</button>
        </template>
        
        <template v-if="task.status === 'in_progress'">
          <button @click="showProgressModal = true" class="btn btn-primary">更新进度</button>
          <button v-if="task.progress === 100" @click="showCompleteModal = true" class="btn bg-green-600 text-white hover:bg-green-700 font-bold px-6">提交验收</button>
          <button @click="showExtensionModal = true" class="btn bg-amber-50 text-amber-700 border border-amber-200 hover:bg-amber-100">申请延期</button>
        </template>
        
        <template v-if="task.status === 'pending_review' && canReview()">
          <button @click="showReviewModal = true" class="btn btn-primary px-8">评分并完成</button>
          <button @click="showReturnModal = true" class="btn btn-danger">验收不通过</button>
          <button @click="rollbackTask" class="btn bg-slate-100 text-slate-600 hover:bg-slate-200 ml-auto font-medium">回撤至进行中</button>
        </template>

        <template v-if="task.status === 'rejected'">
          <button @click="router.push(`/tasks/new?id=${task.id}`)" class="btn btn-primary px-8">重新修改并提交</button>
        </template>

        <!-- 管理员/主管额外权限 -->
        <button v-if="canAdjustCoefficients()" @click="openCoefficientModal" class="btn border-2 border-dashed border-indigo-200 text-indigo-500 hover:border-indigo-500 hover:bg-indigo-50 font-bold ml-auto">调整 I/D/Q 系数</button>
      </div>
    </div>

    <!-- 子任务区块 -->
    <div v-if="(task.subtasks && task.subtasks.length > 0) || canCreateSubtask()" class="card animate-fade-in-up" style="animation-delay: 0.1s">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-xl font-black text-slate-800 flex items-center gap-3">
          <span class="p-2 bg-emerald-100 text-emerald-600 rounded-xl">🌿</span> 子任务拆解
        </h2>
        <button v-if="canCreateSubtask()" @click="router.push(`/tasks/new?parent=${task.id}`)" class="px-4 py-2 bg-indigo-50 text-indigo-600 rounded-xl text-sm font-black border border-indigo-100 hover:bg-indigo-600 hover:text-white transition-all shadow-sm">+ 添加子任务</button>
      </div>

      <div v-if="!task.subtasks || task.subtasks.length === 0" class="text-center py-12 bg-slate-50 rounded-2xl border-2 border-dashed border-slate-200 text-slate-400">
        <p class="font-bold">尚未进行子任务拆解</p>
        <p class="text-xs mt-2">将复杂工作拆解成小的里程碑有助于更好地管理进度</p>
      </div>

      <div v-else class="grid gap-4 sm:grid-cols-2">
        <div v-for="sub in task.subtasks" :key="sub.id" @click="router.push(`/tasks/${sub.id}`)" 
             class="p-5 bg-white border border-slate-100 rounded-2xl hover:shadow-xl hover:border-indigo-200 transition-all cursor-pointer group relative overflow-hidden">
          <div class="absolute top-0 left-0 w-1 h-full bg-slate-100 group-hover:bg-indigo-500 transition-colors"></div>
          <div class="flex justify-between items-start mb-3 pl-2">
            <h3 class="font-black text-slate-800 group-hover:text-indigo-600 truncate pr-2 transition-colors">{{ sub.title }}</h3>
            <span class="px-2.5 py-0.5 rounded-full text-[10px] uppercase font-black tracking-widest shrink-0 shadow-sm" :class="'status-badge status-' + sub.status">
              {{ getStatusText(sub.status) }}
            </span>
          </div>
          <div class="flex items-center gap-5 text-xs text-slate-500 font-bold pl-2">
            <span class="flex items-center gap-1.5"><span class="text-indigo-400">📊</span> {{ sub.progress }}%</span>
            <span class="flex items-center gap-1.5"><span class="text-emerald-400">⚖️</span> B={{ sub.workload_b || '0' }}</span>
          </div>
          <div class="mt-4 h-1.5 bg-slate-100 rounded-full overflow-hidden ml-2">
            <div class="h-full rounded-full transition-all duration-700" 
                 :class="sub.status === 'completed' ? 'bg-emerald-500' : 'bg-indigo-500'" 
                 :style="{ width: `${sub.progress}%` }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 日志区块 -->
    <div class="card animate-fade-in-up" style="animation-delay: 0.2s">
      <h2 class="text-xl font-black text-slate-800 mb-6 flex items-center gap-3">
        <span class="p-2 bg-blue-100 text-blue-600 rounded-xl">📝</span> 任务流转日志
      </h2>
      
      <div v-if="!logs || logs.length === 0" class="text-slate-400 text-center py-8 font-bold">暂无任何操作日志</div>
      
      <div v-else class="relative border-l-2 border-slate-100 ml-6 pl-10 space-y-8 pb-4">
        <div v-for="log in logs" :key="log.id" class="relative group">
          <!-- 时间轴锚点 -->
          <div class="absolute -left-[51px] top-1 w-5 h-5 rounded-full border-4 border-white bg-indigo-500 group-hover:scale-125 transition-transform shadow-md"></div>
          
          <div class="flex justify-between items-start mb-2">
            <div>
              <p class="font-black text-slate-800 text-base flex items-center gap-2">
                {{ getActionText(log.action) }}
                <span v-if="log.progress_after" class="text-xs font-black px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded">进度 {{ log.progress_after }}%</span>
              </p>
              <p class="text-xs text-slate-400 font-bold mt-1 uppercase tracking-wider">{{ log.created_at ? new Date(log.created_at).toLocaleString() : '-' }}</p>
            </div>
          </div>
          
          <div v-if="log.content" class="bg-slate-50 rounded-2xl p-4 text-sm text-slate-600 border border-transparent hover:border-slate-200 transition-colors leading-relaxed shadow-sm">
            {{ log.content }}
          </div>

          <!-- 日志附件 -->
          <div v-if="log.attachments && log.attachments.length > 0" class="flex flex-wrap gap-2 mt-3">
            <div v-for="att in log.attachments" :key="att.id" class="group/att relative">
               <a :href="`/api/attachments/${att.id}/download?token=${authStore.token}`" target="_blank" 
                  class="flex items-center gap-2 px-3 py-2 bg-white border border-slate-100 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all">
                  <span class="text-lg">{{ att.file_type?.startsWith('image/') ? '🖼️' : '📎' }}</span>
                  <div class="max-w-[120px]">
                    <p class="text-xs font-black text-slate-700 truncate">{{ att.filename }}</p>
                    <p class="text-[10px] text-slate-400 font-bold">{{ formatFileSize(att.file_size) }}</p>
                  </div>
               </a>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- MODALS -->

    <!-- 更新进度 Modal -->
    <div v-if="showProgressModal" class="modal-overlay animate-fade-in" @click.self="showProgressModal = false">
      <div class="modal-content animate-fade-in-up">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-black text-slate-800">更新任务进度</h3>
          <button @click="showProgressModal = false" class="text-slate-400 hover:text-slate-600 text-xl">✕</button>
        </div>
        <div class="space-y-6">
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-3">进度百分比 ({{ progressForm.percent }}%)</label>
            <input type="range" v-model.number="progressForm.percent" min="0" max="100" step="5" class="w-full h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600" />
            <div class="flex justify-between text-[10px] text-slate-400 font-bold mt-2">
              <span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span>
            </div>
          </div>
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">进展详细说明 *</label>
            <textarea v-model="progressForm.content" placeholder="请详细描述目前的工作成果、遇到的困难或下一步计划..." rows="4" class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-indigo-200 outline-none transition-all"></textarea>
          </div>
          <div>
              <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">上传凭证 (可选)</label>
              <input type="file" @change="handleProgressFileChange" multiple class="hidden" id="prog-files" />
              <div class="flex flex-wrap gap-2">
                <label for="prog-files" class="w-16 h-16 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400 hover:border-indigo-400 hover:text-indigo-500 cursor-pointer transition-all text-2xl">+</label>
                <div v-for="(f, i) in progressForm.files" :key="i" class="w-16 h-16 border border-indigo-100 rounded-2xl p-1 relative flex items-center justify-center bg-indigo-50">
                   <span class="text-xs font-black text-indigo-600 truncate px-1">{{ f.name }}</span>
                   <button @click="progressForm.files.splice(i, 1)" class="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-[10px]">✕</button>
                </div>
              </div>
          </div>
          <div class="flex gap-4 pt-4">
            <button @click="showProgressModal = false" class="btn bg-slate-100 text-slate-600 flex-1">取消</button>
            <button @click="updateProgress" class="btn btn-primary flex-1">提交进展</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 审批通过 Modal -->
    <div v-if="showApproveModal" class="modal-overlay animate-fade-in" @click.self="showApproveModal = false">
      <div class="modal-content animate-fade-in-up max-w-sm">
        <h3 class="text-xl font-black text-slate-800 mb-6">任务审核定级</h3>
        <div class="space-y-6">
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">重要性系数 I</label>
            <input type="number" v-model.number="approveForm.importance" step="0.1" min="0.5" max="1.5" class="w-full p-3 bg-slate-50 border rounded-xl font-black text-slate-700" />
            <p class="text-[10px] text-slate-400 mt-2 font-bold italic">💡 反映任务对组织的核心贡献度 (0.5-1.5)</p>
          </div>
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">难度系数 D</label>
            <input type="number" v-model.number="approveForm.difficulty" step="0.1" min="0.8" max="1.5" class="w-full p-3 bg-slate-50 border rounded-xl font-black text-slate-700" />
            <p class="text-[10px] text-slate-400 mt-2 font-bold italic">💡 反映任务的技术门槛与复杂性 (0.8-1.5)</p>
          </div>
          <div class="pt-4 flex gap-3">
            <button @click="showApproveModal = false" class="btn bg-slate-100 text-slate-600 flex-1">取消</button>
            <button @click="approveTask" class="btn btn-primary flex-1 shadow-indigo-200">确认通过并立即启动</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 延期申请 Modal -->
    <div v-if="showExtensionModal" class="modal-overlay animate-fade-in" @click.self="showExtensionModal = false">
      <div class="modal-content animate-fade-in-up">
        <h3 class="text-xl font-black text-amber-800 mb-6 flex items-center gap-2"><span>⏳</span> 申请任务延期</h3>
        <div class="space-y-6">
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">期望延期至 *</label>
            <input type="datetime-local" v-model="extensionForm.date" class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-amber-200 transition-all font-bold text-slate-700" />
          </div>
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">延期具体事由 *</label>
            <textarea v-model="extensionForm.reason" rows="4" placeholder="请说明进度滞后的具体客观原因..." class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-amber-200 transition-all text-sm"></textarea>
          </div>
          <div class="flex gap-4 pt-2">
            <button @click="showExtensionModal = false" class="btn bg-slate-100 text-slate-600 flex-1">我再想想</button>
            <button @click="requestExtension" class="btn bg-amber-600 text-white hover:bg-amber-700 flex-1 font-black shadow-lg shadow-amber-200">确认提交申请</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 退回/驳回 Modal -->
    <div v-if="showReturnModal" class="modal-overlay animate-fade-in" @click.self="showReturnModal = false">
      <div class="modal-content animate-fade-in-up max-w-sm">
        <h3 class="text-xl font-black text-red-800 mb-6 flex items-center gap-2"><span>↩️</span> 退回/驳回任务</h3>
        <div class="space-y-6">
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">退回原因/改进建议 *</label>
            <textarea v-model="returnForm.reason" rows="4" placeholder="请输入退回的具体原因或具体的改进要求..." class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-red-200 transition-all text-sm text-slate-600 font-medium"></textarea>
          </div>
          <div class="flex gap-4">
            <button @click="showReturnModal = false" class="btn bg-slate-100 text-slate-600 flex-1">取消</button>
            <button @click="returnTask" class="btn bg-red-600 text-white hover:bg-red-700 flex-1 font-black shadow-lg shadow-red-200">确认退回</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 验收评分 Modal -->
    <div v-if="showReviewModal" class="modal-overlay animate-fade-in" @click.self="showReviewModal = false">
      <div class="modal-content animate-fade-in-up">
        <h3 class="text-xl font-black text-slate-800 mb-6 flex items-center gap-2"><span>🏁</span> 任务验收与评分</h3>
        <div class="space-y-6">
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">质量系数 Q ({{ reviewForm.quality }})</label>
            <div class="flex items-center gap-4">
              <input type="range" v-model.number="reviewForm.quality" min="0" max="1.2" step="0.1" class="flex-1 h-2 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-indigo-600" />
              <span class="w-12 text-center font-black text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg">{{ reviewForm.quality }}</span>
            </div>
            <div class="flex justify-between text-[10px] text-slate-400 font-bold mt-2 uppercase tracking-tight">
               <span>❌ 不合格(0)</span>
               <span>⚠️ 及格(0.8)</span>
               <span>✅ 完美(1.2)</span>
            </div>
          </div>
          <div>
            <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">验收评语</label>
            <textarea v-model="reviewForm.comment" rows="4" placeholder="对实施人的工作表现给予评价..." class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-200 transition-all text-sm"></textarea>
          </div>
          <div class="flex gap-4 pt-2">
            <button @click="showReviewModal = false" class="btn bg-slate-100 text-slate-600 flex-1">取消</button>
            <button @click="reviewTask" class="btn btn-primary flex-1 shadow-lg shadow-indigo-100">确认结项</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 调整系数 Modal -->
    <div v-if="showCoefficientModal" class="modal-overlay animate-fade-in" @click.self="showCoefficientModal = false">
      <div class="modal-content animate-fade-in-up">
        <h3 class="text-xl font-black text-indigo-800 mb-6">动态调整任务系数</h3>
        <div class="grid grid-cols-2 gap-4 mb-6">
           <div>
              <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">重要性 I</label>
              <input type="number" v-model.number="coefficientForm.importance" step="0.05" class="w-full p-3 bg-slate-50 border rounded-xl font-black text-indigo-600" />
           </div>
           <div>
              <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">难度 D</label>
              <input type="number" v-model.number="coefficientForm.difficulty" step="0.05" class="w-full p-3 bg-slate-50 border rounded-xl font-black text-indigo-600" />
           </div>
        </div>
        <div class="mb-6">
           <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">调整原因 *</label>
           <textarea v-model="coefficientForm.reason" placeholder="追溯调整系数必须注明原因以供审计..." class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl text-sm font-medium h-32 focus:ring-2 focus:ring-indigo-100 outline-none"></textarea>
        </div>
        <div class="flex gap-4">
           <button @click="showCoefficientModal = false" class="btn bg-slate-100 text-slate-500 flex-1">取消</button>
           <button @click="updateCoefficients" class="btn btn-primary flex-1 shadow-lg">确认修改</button>
        </div>
      </div>
    </div>

    <!-- 提交验收 Modal -->
    <div v-if="showCompleteModal" class="modal-overlay animate-fade-in" @click.self="showCompleteModal = false">
        <div class="modal-content animate-fade-in-up max-w-md">
            <h3 class="text-xl font-black text-slate-800 mb-6 flex items-center gap-2"><span>🚀</span> 提交任务验收申请</h3>
            <div class="space-y-6">
                <div class="bg-indigo-50 border border-indigo-100 p-4 rounded-2xl flex gap-3 text-indigo-700 text-sm font-bold">
                    <span>💡</span>
                    <p>提交验收后，由于你已完成 100% 进度，主管将收到提醒进行 Q 质量定级。</p>
                </div>
                <div>
                   <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">完成感悟/备注</label>
                   <textarea v-model="completeForm.comment" rows="3" placeholder="简要总结本次任务的产出成果..." class="w-full p-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-indigo-100 transition-all text-sm"></textarea>
                </div>
                <div>
                  <label class="block text-xs font-black text-slate-400 uppercase tracking-widest mb-2">附件资源</label>
                  <input type="file" @change="handleCompleteFileChange" multiple class="hidden" id="comp-files" />
                  <div class="flex flex-wrap gap-2">
                    <label for="comp-files" class="w-16 h-16 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl text-slate-400 hover:border-indigo-400 cursor-pointer text-2xl">+</label>
                    <div v-for="(f, i) in completeForm.files" :key="i" class="w-16 h-16 border border-emerald-100 rounded-2xl p-1 relative flex items-center justify-center bg-emerald-50">
                       <span class="text-[10px] font-black text-emerald-600 truncate px-1">{{ f.name }}</span>
                    </div>
                  </div>
                </div>
                <div class="flex gap-4 pt-2">
                  <button @click="showCompleteModal = false" class="btn bg-slate-100 text-slate-500 flex-1">暂不提交</button>
                  <button @click="completeTask" class="btn btn-primary flex-1">确认提交验收</button>
                </div>
            </div>
        </div>
    </div>

    <!-- 历史记录 Modal -->
    <div v-if="showHistoryModal" class="modal-overlay animate-fade-in" @click.self="showHistoryModal = false">
      <div class="modal-content animate-fade-in-up max-w-2xl">
        <div class="flex justify-between items-center mb-6">
          <h3 class="text-xl font-black text-slate-800">进度演进历史</h3>
          <button @click="showHistoryModal = false" class="text-slate-400 hover:text-slate-600">✕</button>
        </div>
        <div class="max-h-[60vh] overflow-y-auto pr-4 custom-scrollbar">
           <table class="w-full">
             <thead>
               <tr class="text-left text-xs font-black text-slate-400 uppercase tracking-widest border-b border-slate-100">
                 <th class="pb-3 px-2">时间</th>
                 <th class="pb-3 px-2">进度变更</th>
                 <th class="pb-3 px-2">说明</th>
                 <th class="pb-3 px-2">凭证</th>
               </tr>
             </thead>
             <tbody class="divide-y divide-slate-50">
               <tr v-for="h in progressHistory" :key="h.id" class="text-sm font-medium">
                 <td class="py-4 px-2 text-slate-400 tabular-nums">{{ new Date(h.created_at).toLocaleString() }}</td>
                 <td class="py-4 px-2">
                   <span class="text-indigo-600 font-black">{{ h.progress_after }}%</span>
                   <span class="text-[10px] text-slate-300 ml-1">(由 {{ h.progress_before }}%)</span>
                 </td>
                 <td class="py-4 px-2 text-slate-600 max-w-[200px] truncate">{{ h.content || '-' }}</td>
                 <td class="py-4 px-2">
                   <span v-if="h.attachments?.length" class="text-indigo-400">📎 {{ h.attachments.length }}</span>
                   <span v-else class="text-slate-200">-</span>
                 </td>
               </tr>
               <tr v-if="!progressHistory.length">
                 <td colspan="4" class="py-12 text-center text-slate-300 italic">暂无进度变更记录</td>
               </tr>
             </tbody>
           </table>
        </div>
      </div>
    </div>

    <!-- 图片预览 Modal -->
    <div v-if="showPreviewModal" class="modal-overlay bg-black/90 animate-fade-in" @click.self="showPreviewModal = false">
       <div class="relative max-w-5xl max-h-[90vh]">
          <button @click="showPreviewModal = false" class="absolute -top-12 right-0 text-white hover:text-indigo-400 text-3xl">✕</button>
          <img :src="previewUrl" class="rounded-2xl shadow-2xl max-h-[85vh] object-contain" />
       </div>
    </div>

  </div>
</template>

<style scoped>
.glass-stat {
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.glass-stat:hover {
  transform: translateY(-4px);
  background: white;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
}
.stat-label {
  font-size: 10px;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-bottom: 4px;
}
.stat-value {
  font-size: 1.5rem;
  font-weight: 900;
  line-height: 1;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1.5rem;
}
.modal-content {
  background: white;
  padding: 2.5rem;
  border-radius: 2rem;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25);
  max-height: 95vh;
  overflow-y: auto;
}

.status-badge {
  display: inline-flex;
  align-items: center;
}
.status-draft { background: #f1f5f9; color: #64748b; }
.status-pending_approval, .status-pending_leader_approval { background: #fef3c7; color: #d97706; }
.status-pending_submission { background: #f3e8ff; color: #7e22ce; }
.status-in_progress { background: #e0f2fe; color: #0284c7; }
.status-pending_review { background: #f0fdf4; color: #16a34a; }
.status-completed { background: #16a34a; color: white; }
.status-rejected { background: #fee2e2; color: #dc2626; }
.status-cancelled { background: #f1f5f9; color: #94a3b8; }

.animate-fade-in {
  animation: fadeIn 0.4s ease-out forwards;
}
.animate-fade-in-up {
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes fadeInUp { 
  from { opacity: 0; transform: translateY(20px); } 
  to { opacity: 1; transform: translateY(0); } 
}

/* Chrome, Safari, Edge */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
