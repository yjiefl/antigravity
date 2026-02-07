<script setup lang="ts">
/**
 * 任务创建/编辑表单
 */
import { ref, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import api from "../api";

const router = useRouter();
const route = useRoute();

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

// 提交
async function handleSubmit() {
  if (!form.value.title) {
    error.value = "请输入任务标题";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    await api.post("/api/tasks", {
      ...form.value,
      plan_start: form.value.plan_start || null,
      plan_end: form.value.plan_end || null,
    });
    router.push("/tasks");
  } catch (e: any) {
    error.value = e.response?.data?.detail || "创建失败";
  } finally {
    loading.value = false;
  }
}
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
      <h1 class="text-2xl font-bold text-slate-800 mb-6">➕ 新建任务</h1>

      <form @submit.prevent="handleSubmit" class="space-y-6">
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
              type="date"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >计划完成</label
            >
            <input
              v-model="form.plan_end"
              type="date"
              class="w-full px-4 py-3 border border-slate-200 rounded-lg"
            />
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
        <div class="flex gap-4">
          <button
            type="button"
            @click="router.push('/tasks')"
            class="btn btn-secondary flex-1"
          >
            取消
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="btn btn-primary flex-1"
          >
            {{ loading ? "创建中..." : "创建任务" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
