<script setup lang="ts">
/**
 * 申诉审核页面（管理员/经理用）
 */
import { ref, onMounted } from "vue";
import api from "../api";

const appeals = ref<any[]>([]);
const loading = ref(true);
const processingId = ref<string | null>(null);

// 审核表单
const reviewForm = ref({
  id: "",
  status: "" as "approved" | "rejected",
  comment: "",
});
const showReviewDialog = ref(false);

async function loadAppeals() {
  loading.value = true;
  try {
    const response = await api.get("/api/appeals/admin/pending");
    appeals.value = response.data;
  } catch (e) {
    console.error("加载待审核申诉失败", e);
  } finally {
    loading.value = false;
  }
}

function openReview(appeal: any, status: "approved" | "rejected") {
  reviewForm.value = {
    id: appeal.id,
    status: status,
    comment: status === "approved" ? "情况属实，准予撤销考核。" : "",
  };
  showReviewDialog.value = true;
}

async function submitReview() {
  if (!reviewForm.value.comment) {
    alert("请填写审核意见");
    return;
  }

  processingId.value = reviewForm.value.id;
  try {
    await api.post(`/api/appeals/${reviewForm.value.id}/review`, {
      status: reviewForm.value.status,
      review_comment: reviewForm.value.comment,
    });
    showReviewDialog.value = false;
    await loadAppeals(); // 刷新列表
  } catch (e) {
    console.error("审核失败", e);
    alert("处理失败，请重试");
  } finally {
    processingId.value = null;
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("zh-CN");
}

function getReasonLabel(type: string) {
  const map: Record<string, string> = {
    dependency_blocked: "前序阻塞",
    external_factor: "外部因素",
    requirement_change: "需求变更",
    resource_shortage: "资源不足",
    other: "其他",
  };
  return map[type] || type;
}

onMounted(() => {
  loadAppeals();
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h1 class="text-3xl font-bold text-indigo-950 tracking-tight">
        ⚖️ 申诉审核
      </h1>
      <button
        @click="loadAppeals"
        class="p-2.5 bg-white/40 border border-white/60 text-slate-500 hover:text-indigo-600 hover:bg-white rounded-xl transition-all shadow-sm"
        title="刷新列表"
      >
        <span v-if="loading" class="animate-spin inline-block">🔄</span>
        <span v-else>🔄</span>
      </button>
    </div>

    <div
      v-if="loading && appeals.length === 0"
      class="flex flex-col items-center justify-center py-24 gap-4"
    >
      <div
        class="w-12 h-12 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"
      ></div>
      <p class="text-indigo-900/40 font-bold tracking-widest text-sm uppercase">
        正在加载待审核事项...
      </p>
    </div>

    <div
      v-else-if="appeals.length === 0"
      class="glass-card py-24 flex flex-col items-center text-center"
    >
      <div
        class="w-20 h-20 bg-green-50 rounded-3xl flex items-center justify-center text-4xl mb-6"
      >
        🎉
      </div>
      <h3 class="text-xl font-bold text-slate-800">当前无待处理申诉</h3>
      <p class="text-slate-500 mt-2">所有的红牌申诉都已处理完毕，保持状态</p>
    </div>

    <div v-else class="grid grid-cols-1 gap-6">
      <div
        v-for="appeal in appeals"
        :key="appeal.id"
        class="glass-card overflow-hidden group border-l-4 border-l-amber-400"
      >
        <div class="flex flex-col md:flex-row p-6 gap-8">
          <div class="flex-1 space-y-6">
            <div class="flex items-center gap-3">
              <span
                class="px-2 py-1 bg-amber-100 text-amber-700 text-[10px] font-black uppercase tracking-widest rounded"
                >待审核</span
              >
              <h3
                class="font-black text-slate-800 text-xl tracking-tight group-hover:text-amber-600 transition-colors"
              >
                {{ appeal.task_title }}
              </h3>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div class="space-y-3">
                <p
                  class="text-slate-400 uppercase text-[10px] font-black tracking-widest"
                >
                  申诉详情
                </p>
                <div
                  class="bg-slate-50/50 p-4 rounded-2xl border border-slate-100 italic text-slate-700 text-sm leading-relaxed"
                >
                  <span
                    class="inline-block px-2 py-0.5 bg-slate-200 rounded text-[10px] font-bold text-slate-600 mr-2 not-italic"
                  >
                    {{ getReasonLabel(appeal.reason_type) }}
                  </span>
                  "{{ appeal.reason_detail }}"
                </div>
              </div>
              <div class="space-y-3">
                <p
                  class="text-slate-400 uppercase text-[10px] font-black tracking-widest"
                >
                  时间线信息
                </p>
                <div class="space-y-2">
                  <p
                    class="text-xs font-bold text-slate-600 flex items-center gap-2"
                  >
                    <span class="w-2 h-2 rounded-full bg-slate-300"></span>
                    提交时间: {{ formatDate(appeal.created_at) }}
                  </p>
                  <p
                    class="text-[10px] font-bold text-red-400 flex items-center gap-2 uppercase tracking-tighter"
                  >
                    <span
                      class="w-2 h-2 rounded-full bg-red-400 animate-pulse"
                    ></span>
                    失效时间: {{ formatDate(appeal.expires_at) }}
                  </p>
                </div>
              </div>
            </div>

            <div
              v-if="appeal.evidence_urls"
              class="pt-4 border-t border-slate-100 flex items-center justify-between"
            >
              <p
                class="text-slate-400 uppercase text-[10px] font-black tracking-widest"
              >
                附件凭证
              </p>
              <a
                :href="appeal.evidence_urls"
                target="_blank"
                class="px-4 py-1.5 bg-indigo-50 text-indigo-600 rounded-full text-xs font-bold hover:bg-indigo-600 hover:text-white transition-all flex items-center gap-2"
              >
                📎 点击在线查阅
              </a>
            </div>
          </div>

          <div
            class="flex md:flex-col justify-end gap-3 min-w-[140px] border-t md:border-t-0 md:border-l border-slate-100 pt-6 md:pt-0 md:pl-8"
          >
            <button
              @click="openReview(appeal, 'approved')"
              class="flex-1 px-6 py-3 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 transition-all shadow-lg shadow-green-100 active:scale-95"
            >
              准予撤销
            </button>
            <button
              @click="openReview(appeal, 'rejected')"
              class="flex-1 px-6 py-3 bg-white border border-slate-200 text-slate-500 rounded-xl font-bold hover:bg-slate-50 transition-all active:scale-95"
            >
              驳回申诉
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 审核对话框 -->
    <div
      v-if="showReviewDialog"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm"
    >
      <div
        class="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200"
      >
        <div
          class="p-6 border-b border-slate-100 flex items-center justify-between"
        >
          <h3 class="text-xl font-bold text-slate-800">
            {{ reviewForm.status === "approved" ? "准予撤销考核" : "驳回申诉" }}
          </h3>
          <button
            @click="showReviewDialog = false"
            class="text-slate-400 hover:text-slate-600"
          >
            ✕
          </button>
        </div>
        <div class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1"
              >审核意见</label
            >
            <textarea
              v-model="reviewForm.comment"
              rows="4"
              class="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-100 outline-none transition-all resize-none"
              placeholder="请写下审核理由或改进建议..."
            ></textarea>
          </div>
        </div>
        <div class="p-6 bg-slate-50 flex gap-3">
          <button
            @click="showReviewDialog = false"
            class="flex-1 py-2 border border-slate-200 text-slate-600 rounded-xl font-medium"
          >
            取消
          </button>
          <button
            @click="submitReview"
            :disabled="!!processingId"
            class="flex-1 py-2 rounded-xl font-bold text-white transition-all shadow-lg"
            :class="
              reviewForm.status === 'approved'
                ? 'bg-green-600 hover:bg-green-700 shadow-green-100'
                : 'bg-red-500 hover:bg-red-600 shadow-red-100'
            "
          >
            {{ processingId ? "正在处理..." : "确认操作" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
