<script setup lang="ts">
/**
 * 申诉提交弹窗
 */
import { ref, reactive } from "vue";
import api from "../api";

const props = defineProps<{
  card: any;
}>();

const emit = defineEmits(["close", "success"]);

const loading = ref(false);
const error = ref("");

const form = reactive({
  reason_type: "dependency_blocked",
  reason_detail: "",
  evidence_urls: "",
});

const reasonOptions = [
  { value: "dependency_blocked", label: "前序任务阻塞" },
  { value: "external_factor", label: "外部因素（突发状况）" },
  { value: "requirement_change", label: "需求变更/调整" },
  { value: "resource_shortage", label: "资源不足/环境受限" },
  { value: "other", label: "其他原因" },
];

async function handleSubmit() {
  if (!form.reason_detail) {
    error.value = "请填写详细的申诉理由";
    return;
  }

  loading.value = true;
  error.value = "";
  try {
    // 使用 card.appeal_id 提交
    await api.put(`/api/appeals/${props.card.appeal_id}/submit`, form);
    emit("success");
  } catch (e: any) {
    console.error("提交申诉失败", e);
    error.value = e.response?.data?.detail || "提交失败，请重试";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm"
  >
    <div
      class="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in duration-200"
    >
      <!-- 头部 -->
      <div
        class="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-50/50"
      >
        <h3 class="text-xl font-bold text-slate-800">发起申诉</h3>
        <button
          @click="emit('close')"
          class="text-slate-400 hover:text-slate-600 transition-colors"
        >
          ✕
        </button>
      </div>

      <!-- 内容 -->
      <div class="p-6 space-y-4">
        <div class="p-3 bg-red-50 rounded-lg border border-red-100">
          <p class="text-sm font-bold text-red-800 mb-1">
            针对任务：{{ card.task_title }}
          </p>
          <p class="text-xs text-red-600">{{ card.reason_analysis }}</p>
        </div>

        <div
          v-if="error"
          class="p-3 bg-red-100 text-red-700 text-sm rounded-lg"
        >
          {{ error }}
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1"
            >申诉原因类型</label
          >
          <select
            v-model="form.reason_type"
            class="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 outline-none transition-all"
          >
            <option
              v-for="opt in reasonOptions"
              :key="opt.value"
              :value="opt.value"
            >
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1"
            >详细说明</label
          >
          <textarea
            v-model="form.reason_detail"
            rows="4"
            placeholder="请详细描述造成延期的原因..."
            class="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 outline-none transition-all resize-none"
          ></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1"
            >相关证据链接（可选）</label
          >
          <input
            v-model="form.evidence_urls"
            type="text"
            placeholder="例如：文档或邮件链接"
            class="w-full px-4 py-2 border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-100 focus:border-indigo-500 outline-none transition-all"
          />
        </div>
      </div>

      <!-- 底部 -->
      <div class="p-6 bg-slate-50 flex gap-3">
        <button
          @click="emit('close')"
          class="flex-1 py-2.5 border border-slate-200 text-slate-600 rounded-xl font-medium hover:bg-white transition-all"
        >
          取消
        </button>
        <button
          @click="handleSubmit"
          :disabled="loading"
          class="flex-[2] py-2.5 bg-indigo-600 text-white rounded-xl font-bold shadow-lg shadow-indigo-200 hover:bg-indigo-700 active:scale-95 transition-all disabled:opacity-50 disabled:active:scale-100"
        >
          {{ loading ? "正在提交..." : "确认提交" }}
        </button>
      </div>
    </div>
  </div>
</template>
