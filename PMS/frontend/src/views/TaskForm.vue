<script setup lang="ts">
/**
 * 任务创建/编辑表单
 */
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import api from "../api";

const router = useRouter();
const route = useRoute();
const taskId = route.query.id as string;
const isEdit = !!taskId;

// 表单数据
const form = ref({
  title: "",
  description: "",
  task_type: "performance",
  category: "other",
  plan_start: "",
  plan_end: "",
});

const loading = ref(false);
const error = ref("");

// 类型选项
const taskTypes = [
  { value: "performance", label: "绩效任务" },
  { value: "daily", label: "日常任务" },
];

const categories = [
  { value: "project", label: "项目类" },
  { value: "routine", label: "常规类" },
  { value: "urgent", label: "紧急类" },
  { value: "staged", label: "阶段性" },
  { value: "other", label: "其他" },
];

const dateError = ref("");

// 实时校验日期
function validateDates() {
  dateError.value = "";
  
  if (form.value.plan_start && form.value.plan_end) {
    const start = new Date(form.value.plan_start);
    const end = new Date(form.value.plan_end);
    if (end < start) {
      dateError.value = "计划完成时间不能早于计划开始时间";
      return false;
    }
  }
  return true;
}

// 提交
async function handleSubmit(submit = false) {
  if (!form.value.title) {
    error.value = "请输入任务标题";
    return;
  }
  
  // 再次校验日期
  if (!validateDates()) {
     return;
  }


  
  // 仅在非编辑模式下校验开始时间是否早于当日（可选，视需求而定，这里保留但放宽到分钟？）
  // 或者用户可能需要补录过去的某个任务，所以这个校验可能需要谨慎。
  // 原有逻辑: if (start < now && !isEdit) ...
  // 这里暂时保持原有业务逻辑的意图，但要注意 datetime 比较
  /* 
  if (form.value.plan_start) {
    const start = new Date(form.value.plan_start);
    if (start < now && !isEdit) {
        // 允许补录，或者提示即可？
        // error.value = "计划开始时间已过";
        // return;
    }
  }
  */

  loading.value = true;
  error.value = "";

  try {
    let res;
    // Pydantic 能处理 ISO 字符串，直接传
    const taskData = {
      ...form.value,
      plan_start: form.value.plan_start || null,
      plan_end: form.value.plan_end || null,
    };

    if (isEdit) {
      res = await api.put(`/api/tasks/${taskId}`, taskData);
    } else {
      res = await api.post("/api/tasks", taskData);
    }
    
    // 如果选择直接提交
    const currentId = isEdit ? taskId : res.data?.id;
    if (submit && currentId) {
      await api.post(`/api/tasks/${currentId}/submit`);
    }
    
    router.push("/tasks");
  } catch (e: any) {
    error.value = e.response?.data?.detail || "创建失败";
  } finally {
    loading.value = false;
  }
}

async function loadExistingTask() {
  if (!isEdit) return;
  loading.value = true;
  try {
    const res = await api.get(`/api/tasks/${taskId}`);
    const t = res.data;
    form.value = {
      title: t.title,
      description: t.description || "",
      task_type: t.task_type,
      category: t.category,
      // 转换为 datetime-local 格式: YYYY-MM-DDThh:mm
      plan_start: t.plan_start ? t.plan_start.slice(0, 16) : "",
      plan_end: t.plan_end ? t.plan_end.slice(0, 16) : "",
    };
  } catch (e) {
    error.value = "加载任务数据失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadExistingTask();
});
</script>

<template>
  <div class="max-w-2xl mx-auto space-y-6">
    <!-- 返回 -->
    <button
      @click="router.push('/tasks')"
      class="text-slate-500 hover:text-slate-700"
    >
      ← 返回列表
    </button>

    <!-- 表单卡片 -->
    <div class="card">
      <h1 class="text-2xl font-bold text-slate-800 mb-6">
        {{ isEdit ? "📝 编辑任务" : "➕ 新建任务" }}
      </h1>

      <form @submit.prevent="handleSubmit(false)" class="space-y-6">
        <!-- 任务标题 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2"
            >任务标题 *</label
          >
          <input
            v-model="form.title"
            type="text"
            placeholder="请输入任务标题"
            class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
          />
        </div>

        <!-- 任务描述 -->
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2"
            >任务描述</label
          >
          <textarea
            v-model="form.description"
            rows="4"
            placeholder="请输入任务描述（建议遵循 5W2H 原则）"
            class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
          ></textarea>
        </div>

        <!-- 类型和分类 -->
        <div class="grid md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >任务类型</label
            >
            <select
              v-model="form.task_type"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg"
            >
              <option v-for="t in taskTypes" :key="t.value" :value="t.value">
                {{ t.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >任务分类</label
            >
            <select
              v-model="form.category"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg"
            >
              <option v-for="c in categories" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </select>
          </div>
        </div>

          <!-- 时间 -->
        <div class="grid md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >计划开始</label
            >
            <input
              v-model="form.plan_start"
              type="datetime-local"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg"
              @input="validateDates"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >计划完成</label
            >
            <input
              v-model="form.plan_end"
              type="datetime-local"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg"
              :class="{'border-red-500 focus:border-red-500 focus:ring-red-200': dateError}"
              @input="validateDates"
            />
            <p v-if="dateError" class="text-xs text-red-500 mt-1 font-bold">{{ dateError }}</p>
          </div>
        </div>

        <!-- 错误提示 -->
        <div
          v-if="error"
          class="text-red-500 text-sm bg-red-50 py-2 px-4 rounded-lg"
        >
          {{ error }}
        </div>

        <!-- 按钮 -->
        <div class="flex flex-col sm:flex-row gap-4">
          <button
            type="button"
            @click="router.push('/tasks')"
            class="btn btn-secondary flex-1 order-3 sm:order-1"
          >
            取消
          </button>
          <button
            type="button"
            @click="handleSubmit(false)"
            :disabled="loading"
            class="btn bg-indigo-100 text-indigo-700 hover:bg-indigo-200 flex-1 order-2"
          >
            {{ loading ? "保存中..." : "保存草稿" }}
          </button>
          <button
            type="button"
            @click="handleSubmit(true)"
            :disabled="loading"
            class="btn btn-primary flex-1 order-1 sm:order-3"
          >
            {{ loading ? "提交中..." : "直接提交" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
