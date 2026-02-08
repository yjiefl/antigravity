<template>
  <div class="space-y-6">
    <!-- Header -->
    <div
      class="flex flex-col md:flex-row justify-between items-start md:items-center gap-6"
    >
      <div>
        <h1 class="text-3xl font-bold text-indigo-950 tracking-tight">
          📊 任务进度甘特图
        </h1>
        <p class="text-slate-500 mt-1 font-medium">
          可视化查看项目任务的时间排期与进度状态
        </p>
      </div>

      <div class="flex items-center gap-3">
        <button @click="fetchTasks" class="btn btn-secondary border-indigo-200">
          🔄 刷新数据
        </button>
      </div>
    </div>

    <!-- Chart Container -->
    <div
      class="glass-card overflow-hidden min-h-[600px] relative p-6 backdrop-blur-2xl"
    >
      <div
        v-if="loading"
        class="absolute inset-0 flex flex-col items-center justify-center bg-white/40 z-10 gap-4"
      >
        <div
          class="w-12 h-12 border-4 border-indigo-100 border-t-indigo-600 rounded-full animate-spin"
        ></div>
        <p
          class="text-indigo-900/40 font-bold uppercase tracking-widest text-xs"
        >
          正在加载甘特图数据...
        </p>
      </div>

      <div class="relative z-10">
        <GanttChart
          v-if="!loading"
          :tasks="tasks"
          :view-mode="viewMode"
          @change-mode="(m) => (viewMode = m)"
          @task-click="handleTaskClick"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import api from "../api";
// @ts-ignore
import GanttChart from "../components/GanttChart.vue";

const router = useRouter();
const tasks = ref<any[]>([]);
const loading = ref(true);
const viewMode = ref("Week");

const fetchTasks = async () => {
  loading.value = true;
  try {
    // 获取所有任务（分页限制稍大一些）
    const response = await api.get("/api/tasks", {
      params: { limit: 100 },
    });
    // 过滤并映射数据
    tasks.value = response.data;
  } catch (error) {
    console.error("Failed to fetch tasks:", error);
  } finally {
    loading.value = false;
  }
};

const handleTaskClick = (task: any) => {
  router.push(`/tasks/${task.id}`);
};

onMounted(() => {
  fetchTasks();
});
</script>
