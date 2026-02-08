<script setup lang="ts">
/**
 * 仪表盘页面
 *
 * 展示任务概览、风险预警、快速操作
 */
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import api from "../api";

const router = useRouter();
const authStore = useAuthStore();

// 统计数据
const stats = ref({
  totalTasks: 0,
  inProgress: 0,
  pendingReview: 0,
  overdue: 0,
  pendingApproval: 0
});

// 任务列表
const riskTasks = ref<any[]>([]);
const myTasks = ref<any[]>([]);
const pendingApprovalTasks = ref<any[]>([]);

// 加载数据
async function loadData() {
  try {
    // 获取任务列表 (获取更多以进行前端筛选，实际项目应使用后端聚合接口)
    const response = await api.get("/api/tasks", {
      params: { limit: 100 },
    });
    const tasks = response.data;
    const userId = authStore.user?.id;

    // 计算统计
    stats.value.totalTasks = tasks.length;
    stats.value.inProgress = tasks.filter(
      (t: any) => t.status === "in_progress",
    ).length;
    stats.value.pendingReview = tasks.filter(
      (t: any) => t.status === "pending_review",
    ).length;
    stats.value.pendingApproval = tasks.filter(
      (t: any) => t.status === "pending_approval",
    ).length;

    // 风险任务（逾期或进度滞后）
    const now = new Date();
    riskTasks.value = tasks
      .filter((t: any) => {
        if (t.status === "completed" || t.status === "rejected" || t.status === "cancelled") return false;
        if (t.plan_end && new Date(t.plan_end) < now) return true;
        return false;
      })
      .slice(0, 5);

    stats.value.overdue = riskTasks.value.length;

    // 我的任务
    myTasks.value = tasks
      .filter((t: any) => t.executor_id === userId || t.owner_id === userId)
      .slice(0, 5);
      
    // 待审批任务 (如果是管理员，显示所有待审批；否则显示自己提交的)
    if (authStore.isManager) {
        pendingApprovalTasks.value = tasks.filter((t: any) => t.status === 'pending_approval' || t.status === 'pending_review').slice(0, 5);
    } else {
        pendingApprovalTasks.value = tasks.filter((t: any) => (t.status === 'pending_approval' || t.status === 'pending_review') && t.creator_id === userId).slice(0, 5);
    }

  } catch (e) {
    console.error("加载数据失败", e);
  }
}

function navigateTo(status: string) {
    router.push({ path: '/tasks', query: { status } });
}



// 获取状态文本
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

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="space-y-6">
    <!-- 欢迎语 -->
    <div
      class="flex flex-col md:flex-row md:items-center justify-between gap-4"
    >
      <div>
        <h1 class="text-3xl font-bold text-indigo-950 tracking-tight">
          你好，{{ authStore.user?.realName }} ✨
        </h1>
        <p class="text-slate-500 mt-1 font-medium italic">
          欢迎回到计划管理控制台
        </p>
      </div>
      <button
        @click="router.push('/tasks/new')"
        class="btn btn-primary shadow-indigo-200"
      >
        ➕ 新建任务
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 lg:grid-cols-5 gap-4">
      <div @click="router.push('/tasks')" class="glass-card p-4 flex flex-col justify-between group cursor-pointer hover:bg-white/60 transition-colors">
        <span class="text-slate-400 group-hover:scale-110 transition-transform duration-300 w-fit">📁</span>
        <div class="mt-2">
          <p class="text-slate-900/60 text-xs font-bold uppercase tracking-widest">总任务</p>
          <p class="text-2xl font-black text-slate-700 mt-1 tracking-tighter">{{ stats.totalTasks }}</p>
        </div>
      </div>
      
      <div @click="navigateTo('pending_approval')" class="glass-card p-4 flex flex-col justify-between group cursor-pointer hover:bg-white/60 transition-colors">
        <span class="text-amber-400 group-hover:scale-110 transition-transform duration-300 w-fit">⏳</span>
        <div class="mt-2">
          <p class="text-amber-900/60 text-xs font-bold uppercase tracking-widest">待审批</p>
          <p class="text-2xl font-black text-amber-600 mt-1 tracking-tighter">{{ stats.pendingApproval }}</p>
        </div>
      </div>

      <div @click="navigateTo('in_progress')" class="glass-card p-4 flex flex-col justify-between group cursor-pointer hover:bg-white/60 transition-colors">
        <span class="text-blue-400 group-hover:scale-110 transition-transform duration-300 w-fit">⚡</span>
        <div class="mt-2">
          <p class="text-blue-900/60 text-xs font-bold uppercase tracking-widest">进行中</p>
          <p class="text-2xl font-black text-blue-600 mt-1 tracking-tighter">{{ stats.inProgress }}</p>
        </div>
      </div>
      
      <div @click="navigateTo('pending_review')" class="glass-card p-4 flex flex-col justify-between group cursor-pointer hover:bg-white/60 transition-colors">
        <span class="text-purple-400 group-hover:scale-110 transition-transform duration-300 w-fit">👁️</span>
        <div class="mt-2">
          <p class="text-purple-900/60 text-xs font-bold uppercase tracking-widest">待验收</p>
          <p class="text-2xl font-black text-purple-600 mt-1 tracking-tighter">{{ stats.pendingReview }}</p>
        </div>
      </div>
      
      <div class="glass-card p-4 border-red-100/50 flex flex-col justify-between group cursor-pointer hover:bg-red-50/30 transition-colors">
        <span class="text-red-400 group-hover:scale-110 transition-transform duration-300 w-fit">🚨</span>
        <div class="mt-2">
          <p class="text-red-900/60 text-xs font-bold uppercase tracking-widest">风险预警</p>
          <p class="text-2xl font-black text-red-500 mt-1 tracking-tighter">{{ stats.overdue }}</p>
        </div>
      </div>
    </div>

    <div class="grid lg:grid-cols-3 gap-6">
      
      <!-- 待我处理 / 待审批 (占用 1 列) -->
      <div class="glass-card overflow-hidden flex flex-col h-full col-span-1">
        <div class="p-4 border-b border-white/20 bg-white/30 flex items-center justify-between">
          <h2 class="text-base font-bold text-slate-800">📌 待处理事项</h2>
          <span class="text-xs font-bold bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">{{ pendingApprovalTasks.length }}</span>
        </div>
        <div class="p-4 flex-1 overflow-y-auto max-h-[400px]">
             <div v-if="pendingApprovalTasks.length === 0" class="text-slate-400 text-center py-8 text-sm">
                🎉 无待处理事项
             </div>
             <div v-else class="space-y-3">
                <div v-for="task in pendingApprovalTasks" :key="task.id" @click="router.push(`/tasks/${task.id}`)" 
                    class="p-3 bg-white/50 rounded-xl border border-transparent hover:border-amber-200 hover:shadow-sm cursor-pointer transition-all">
                    <div class="flex justify-between items-start mb-1">
                        <span class="text-xs font-bold px-1.5 py-0.5 rounded text-white" 
                            :class="task.status === 'pending_approval' ? 'bg-amber-500' : 'bg-purple-500'">
                            {{ task.status === 'pending_approval' ? '待审批' : '待验收' }}
                        </span>
                        <span class="text-xs text-slate-400">{{ new Date(task.created_at).toLocaleDateString() }}</span>
                    </div>
                    <p class="font-bold text-slate-800 text-sm line-clamp-2 mb-1">{{ task.title }}</p>
                    <p class="text-xs text-slate-500">{{ task.creator?.realName || 'Unknown' }} 提交</p>
                </div>
             </div>
        </div>
      </div>

      <!-- 风险与进行中 (占用 2 列) -->
      <div class="lg:col-span-2 space-y-6">
          
        <!-- 风险任务 -->
        <div class="glass-card overflow-hidden">
            <div class="p-4 border-b border-white/20 bg-white/30 flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-800">🚨 风险预警</h2>
            </div>
            <div class="p-4">
            <div
                v-if="riskTasks.length === 0"
                class="text-slate-400 text-center py-8 text-sm"
            >
                ✅ 暂无风险任务，继续保持！
            </div>
            <div v-else class="space-y-2">
                <div
                v-for="task in riskTasks"
                :key="task.id"
                @click="router.push(`/tasks/${task.id}`)"
                class="flex items-center gap-3 p-3 bg-red-50/50 hover:bg-red-50 rounded-xl cursor-pointer transition-all border border-transparent hover:border-red-100"
                >
                <div class="w-8 h-8 rounded-lg bg-red-100 flex items-center justify-center text-red-500 text-sm">⚠️</div>
                <div class="flex-1 min-w-0">
                    <div class="flex justify-between">
                        <p class="font-bold text-slate-800 text-sm truncate">{{ task.title }}</p>
                        <span class="text-xs text-red-500 font-bold">{{ task.plan_end ? new Date(task.plan_end).toLocaleDateString() : '-' }} 截止</span>
                    </div>
                    <div class="w-full h-1 bg-red-100 rounded-full mt-1.5">
                        <div class="h-full bg-red-500 rounded-full" :style="{ width: task.progress + '%' }"></div>
                    </div>
                </div>
                </div>
            </div>
            </div>
        </div>

        <!-- 我的任务 -->
        <div class="glass-card overflow-hidden">
            <div class="p-4 border-b border-white/20 bg-white/30 flex items-center justify-between">
            <h2 class="text-base font-bold text-slate-800">📋 我的任务</h2>
            <button @click="router.push('/tasks')" class="text-xs text-indigo-600 hover:underline">查看全部</button>
            </div>
            <div class="p-4">
            <div v-if="myTasks.length === 0" class="text-slate-400 text-center py-8 text-sm">
                暂无任务
            </div>
            <div v-else class="space-y-2">
                <div v-for="task in myTasks" :key="task.id" @click="router.push(`/tasks/${task.id}`)"
                class="flex items-center gap-3 p-3 bg-white/40 hover:bg-white/80 rounded-xl cursor-pointer transition-all">
                <span class="w-2 h-2 rounded-full" 
                    :class="{
                        'bg-blue-500': task.status === 'in_progress',
                        'bg-amber-500': task.status === 'pending_approval',
                        'bg-green-500': task.status === 'completed',
                        'bg-slate-300': task.status === 'draft'
                    }"></span>
                <div class="flex-1 min-w-0">
                    <p class="font-bold text-slate-800 text-sm truncate mb-0.5">{{ task.title }}</p>
                    <div class="flex items-center gap-2 text-xs text-slate-500">
                        <span>{{ getStatusText(task.status) }}</span>
                        <span>•</span>
                        <span>进度 {{ task.progress }}%</span>
                    </div>
                </div>
                </div>
            </div>
            </div>
        </div>
        
      </div>
    </div>
  </div>
</template>
