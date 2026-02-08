<template>
  <div
    class="gantt-wrapper w-full overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow p-4"
  >
    <div class="flex justify-end mb-4 space-x-2">
      <button
        v-for="mode in modes"
        :key="mode"
        @click="$emit('change-mode', mode)"
        :class="[
          'px-3 py-1 text-sm rounded-md transition-colors',
          currentMode === mode
            ? 'bg-blue-600 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200',
        ]"
      >
        {{ mode === "Day" ? "按日" : mode === "Week" ? "按周" : "按月" }}
      </button>
    </div>

    <svg ref="ganttSvg" class="w-full"></svg>

    <div v-if="tasks.length === 0" class="text-center text-gray-500 py-10">
      暂无计划任务数据
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue";
import Gantt from "frappe-gantt";
import dayjs from "dayjs";

// 引入样式 (如果是 npm 安装，可能需要手动引入 css 或在 main.ts 全局引)
// 这里假设通过 vite 自动处理或手动 import
import "frappe-gantt/dist/frappe-gantt.css";

const props = defineProps<{
  tasks: any[];
  viewMode: string;
}>();

const emit = defineEmits(["change-mode", "task-click"]);

const ganttSvg = ref<SVGSVGElement | null>(null);
const ganttInstance = ref<any>(null);
const modes = ["Day", "Week", "Month"];
const currentMode = ref(props.viewMode || "Week");

// 任务状态颜色映射（通过 custom_class）
const getTaskClass = (status: string) => {
  /* Removed unused map */
  // done: "bar-completed", ...

  // 简单映射
  if (status === "completed") return "bar-completed";
  if (status === "in_progress") return "bar-running";
  if (status === "pending_review") return "bar-review";
  if (status === "pending_approval") return "bar-draft"; // using draft color
  return "bar-draft";
};

const renderGantt = () => {
  if (!props.tasks || !props.tasks.length || !ganttSvg.value) return;

  // 转换数据格式
  // Frappe Gantt 格式: { id, name, start, end, progress, dependencies, custom_class }
  const formattedTasks = props.tasks.map((t) => {
    let start = t.plan_start || t.created_at;
    let end = t.plan_end || t.updated_at || start;

    // 确保日期有效
    if (!dayjs(start).isValid()) start = dayjs().format("YYYY-MM-DD");
    if (!dayjs(end).isValid())
      end = dayjs(start).add(1, "day").format("YYYY-MM-DD");

    // 确保 end >= start + 1 hour/day for visibility
    if (dayjs(end).diff(dayjs(start), "hour") < 1) {
      end = dayjs(start).add(1, "day").format("YYYY-MM-DD");
    }

    return {
      id: t.id,
      name: t.title,
      start: dayjs(start).format("YYYY-MM-DD"),
      end: dayjs(end).format("YYYY-MM-DD"),
      progress: t.progress || 0,
      dependencies: t.parent_id ? "" : "", // 暂不支持依赖连线，因数据模型无前置任务字段
      custom_class: getTaskClass(t.status),
      // 额外数据供 popup 使用
      _raw: t,
    };
  });

  // 清除旧实例DOM副作用（frappe-gantt 直接操作 SVG，可能需要重置）
  ganttSvg.value.innerHTML = "";

  ganttInstance.value = new Gantt(ganttSvg.value, formattedTasks, {
    header_height: 50,
    column_width: 30,
    step: 24,
    view_modes: modes,
    bar_height: 25,
    bar_corner_radius: 4,
    arrow_curve: 5,
    padding: 18,
    view_mode: currentMode.value,
    date_format: "YYYY-MM-DD",
    language: "zh",
    custom_popup_html: function (task: any) {
      const t = task._raw;
      return `
        <div class="p-2 w-64 text-sm">
          <div class="font-bold mb-1">${t.title}</div>
          <div class="text-gray-300 text-xs mb-2">${t.description || "无描述"}</div>
          <div class="grid grid-cols-2 gap-2 text-xs">
            <div>状态: ${getStatusText(t.status)}</div>
            <div>进度: ${t.progress}%</div>
            <div>开始: ${task.start}</div>
            <div>结束: ${task.end}</div>
          </div>
        </div>
      `;
    },
    on_click: (task: any) => {
      emit("task-click", task._raw);
    },
  });
};

watch(
  () => props.tasks,
  () => {
    renderGantt();
  },
  { deep: true },
);

watch(
  () => props.viewMode,
  (newVal) => {
    currentMode.value = newVal;
    if (ganttInstance.value) {
      ganttInstance.value.change_view_mode(newVal);
    }
  },
);

onMounted(() => {
  renderGantt();
});
// 状态文本辅助函数
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
</script>

<style>
/* 覆盖 Frappe Gantt 默认样式以适配 Dark Mode 和 Tailwind */
.gantt-container {
  font-family: inherit;
}

.bar-completed .bar {
  fill: #10b981 !important;
}
.bar-completed .bar-progress {
  fill: #059669 !important;
}

.bar-running .bar {
  fill: #3b82f6 !important;
}
.bar-running .bar-progress {
  fill: #2563eb !important;
}

.bar-review .bar {
  fill: #f59e0b !important;
}
.bar-review .bar-progress {
  fill: #d97706 !important;
}

.bar-draft .bar {
  fill: #9ca3af !important;
}

/* Popup */
.gantt-container .popup-wrapper {
  background: #1f2937;
  color: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  border-radius: 0.5rem;
  padding: 0;
  opacity: 0.95;
}

.gantt-container .grid-header .grid-row {
  fill: transparent;
}
.gantt-container .grid-row {
  fill: transparent;
}
/* Dark mode adjust if needed */
</style>
