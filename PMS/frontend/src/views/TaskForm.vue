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

/**
 * 将 Date 转换为 datetime-local 格式的本地时间字符串
 * 格式: YYYY-MM-DDTHH:mm
 */
function toLocalDateTimeString(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// 表单数据
const form = ref({
  title: "",
  description: "",
  task_type: "performance",
  category: "other",
  plan_start: toLocalDateTimeString(new Date()),
  plan_end: toLocalDateTimeString(new Date(Date.now() + 24 * 60 * 60 * 1000)),
  reviewer_id: "",
  owner_id: "",
  executor_id: "",
});

const users = ref<any[]>([]);
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
async function handleSubmit(mode: "save" | "submit" | "pending" = "save") {
  if (!form.value.title) {
    error.value = "请输入任务标题";
    return;
  }
  if (!form.value.reviewer_id) {
    error.value = "请选择审批人";
    return;
  }

  if (!validateDates()) {
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    let res;
    const taskData = {
      ...form.value,
      reviewer_id: form.value.reviewer_id || null,
      owner_id: form.value.owner_id || null,
      executor_id: form.value.executor_id || null,
      plan_start: form.value.plan_start || null,
      plan_end: form.value.plan_end || null,
    };

    if (isEdit) {
      res = await api.put(`/api/tasks/${taskId}`, taskData);
    } else {
      res = await api.post("/api/tasks", taskData);
    }

    const currentId = isEdit ? taskId : res.data?.id;

    if (mode === "submit" && currentId) {
      await api.post(`/api/tasks/${currentId}/submit`);
    } else if (mode === "pending" && currentId) {
      await api.post(`/api/tasks/${currentId}/mark-pending`);
    }

    router.push("/tasks");
  } catch (e: any) {
    console.error("提交任务失败", e);
    const detail = e.response?.data?.detail;
    if (detail) {
      error.value =
        typeof detail === "string" ? detail : JSON.stringify(detail);
    } else {
      error.value = e.message || "操作失败";
    }
  } finally {
    loading.value = false;
  }
}

async function fetchUsers() {
  try {
    const res = await api.get("/api/users");
    users.value = res.data;
  } catch (e) {
    console.error("加载用户失败", e);
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
      plan_start: t.plan_start ? t.plan_start.slice(0, 16) : "",
      plan_end: t.plan_end ? t.plan_end.slice(0, 16) : "",
      reviewer_id: t.reviewer_id || "",
      owner_id: t.owner_id || "",
      executor_id: t.executor_id || "",
    };
  } catch (e) {
    error.value = "加载任务数据失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchUsers();
  loadExistingTask();
});
</script>

<template>
  <div class="max-w-4xl mx-auto space-y-6">
    <button
      @click="router.push('/tasks')"
      class="text-slate-500 hover:text-slate-700"
    >
      ← 返回列表
    </button>

    <div class="card bg-white p-8 rounded-2xl shadow-sm">
      <h1 class="text-2xl font-bold text-slate-800 mb-6">
        {{ isEdit ? "📝 编辑任务" : "➕ 新建任务" }}
      </h1>

      <form @submit.prevent="handleSubmit('save')" class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2"
            >任务标题 *</label
          >
          <input
            v-model="form.title"
            type="text"
            placeholder="请输入任务标题"
            class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-2"
            >任务描述</label
          >
          <textarea
            v-model="form.description"
            rows="4"
            placeholder="请输入任务描述"
            class="w-full px-4 py-3 border border-slate-200 rounded-lg focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 outline-none"
          ></textarea>
        </div>

        <div class="grid md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >任务类型</label
            >
            <select
              v-model="form.task_type"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
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
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
            >
              <option v-for="c in categories" :key="c.value" :value="c.value">
                {{ c.label }}
              </option>
            </select>
          </div>
        </div>

        <div class="grid md:grid-cols-3 gap-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >审批人/主管 *</label
            >
            <select
              v-model="form.reviewer_id"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
            >
              <option value="">请选择审批人</option>
              <option v-for="u in users" :key="u.id" :value="u.id">
                {{ u.real_name }} (@{{ u.username }})
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >负责人</label
            >
            <select
              v-model="form.owner_id"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
            >
              <option value="">（默认为自己）</option>
              <option v-for="u in users" :key="u.id" :value="u.id">
                {{ u.real_name }} (@{{ u.username }})
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >实施人</label
            >
            <select
              v-model="form.executor_id"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
            >
              <option value="">（待认领或指派）</option>
              <option v-for="u in users" :key="u.id" :value="u.id">
                {{ u.real_name }} (@{{ u.username }})
              </option>
            </select>
          </div>
        </div>

        <div class="grid md:grid-cols-2 gap-6">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >计划开始</label
            >
            <input
              v-model="form.plan_start"
              type="datetime-local"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
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
              class="w-full px-4 py-3 border border-slate-200 rounded-lg outline-none"
              :class="{ 'border-red-500': dateError }"
              @input="validateDates"
            />
            <p v-if="dateError" class="text-xs text-red-500 mt-1 font-bold">
              {{ dateError }}
            </p>
          </div>
        </div>

        <div
          v-if="error"
          class="text-red-500 text-sm bg-red-50 py-2 px-4 rounded-lg"
        >
          {{ error }}
        </div>

        <div
          class="flex flex-col sm:flex-row gap-4 pt-4 border-t border-slate-100"
        >
          <button
            type="button"
            @click="router.push('/tasks')"
            class="btn py-3 px-6 bg-slate-100 text-slate-700 hover:bg-slate-200 flex-1 transition-colors"
          >
            取消
          </button>

          <button
            type="button"
            @click="handleSubmit('save')"
            :disabled="loading"
            class="btn py-3 px-6 bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 flex-1 transition-colors"
          >
            {{ loading ? "保存中..." : "仅保存" }}
          </button>

          <button
            type="button"
            @click="handleSubmit('pending')"
            :disabled="loading"
            class="btn py-3 px-6 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 flex-1 transition-colors"
          >
            {{ loading ? "提交中..." : "标记待提交" }}
          </button>

          <button
            type="button"
            @click="handleSubmit('submit')"
            :disabled="loading"
            class="btn py-3 px-6 bg-indigo-600 text-white hover:bg-indigo-700 flex-1 transition-colors"
          >
            {{ loading ? "提交中..." : "直接提交" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
