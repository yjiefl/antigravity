<script setup lang="ts">
/**
 * 绩效统计页面
 */
import { ref, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import api from "../api";

const authStore = useAuthStore();

const personalKpi = ref<any>(null);
const ranking = ref<any[]>([]);
const loading = ref(true);

async function loadKpi() {
  loading.value = true;
  try {
    const userId = authStore.user?.id;
    if (userId) {
      const [kpiRes, rankRes] = await Promise.all([
        api.get(`/api/kpi/personal/${userId}`),
        api.get("/api/kpi/ranking", { params: { limit: 10 } }),
      ]);
      personalKpi.value = kpiRes.data;
      ranking.value = rankRes.data;
    }
  } catch (e) {
    console.error("加载 KPI 失败", e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadKpi();
});
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-800">📈 绩效统计</h1>

    <div v-if="loading" class="text-center py-12 text-slate-400">加载中...</div>

    <template v-else>
      <!-- 个人绩效 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">我的绩效</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="bg-indigo-50 rounded-lg p-4 text-center">
            <p class="text-sm text-indigo-600">累计得分</p>
            <p class="text-3xl font-bold text-indigo-700">
              {{ personalKpi?.total_score || 0 }}
            </p>
          </div>
          <div class="bg-slate-50 rounded-lg p-4 text-center">
            <p class="text-sm text-slate-600">完成任务</p>
            <p class="text-3xl font-bold text-slate-800">
              {{ personalKpi?.task_count || 0 }}
            </p>
          </div>
          <div class="bg-green-50 rounded-lg p-4 text-center">
            <p class="text-sm text-green-600">准时率</p>
            <p class="text-3xl font-bold text-green-700">
              {{ ((personalKpi?.timeliness_index || 0) * 100).toFixed(0) }}%
            </p>
          </div>
          <div class="bg-red-50 rounded-lg p-4 text-center">
            <p class="text-sm text-red-600">红牌率</p>
            <p class="text-3xl font-bold text-red-700">
              {{ ((personalKpi?.red_card_rate || 0) * 100).toFixed(1) }}%
            </p>
          </div>
        </div>
      </div>

      <!-- 排行榜 -->
      <div class="card">
        <h2 class="text-lg font-semibold text-slate-800 mb-4">🏆 难度贡献榜</h2>
        <div
          v-if="ranking.length === 0"
          class="text-slate-400 text-center py-4"
        >
          暂无数据
        </div>
        <div v-else class="space-y-3">
          <div
            v-for="(item, index) in ranking"
            :key="item.user_id"
            class="flex items-center gap-4 p-3 bg-slate-50 rounded-lg"
          >
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center font-bold"
              :class="{
                'bg-yellow-400 text-white': index === 0,
                'bg-slate-300 text-white': index === 1,
                'bg-orange-400 text-white': index === 2,
                'bg-slate-200 text-slate-600': index > 2,
              }"
            >
              {{ index + 1 }}
            </div>
            <div class="flex-1">
              <p class="font-medium text-slate-800">{{ item.real_name }}</p>
              <p class="text-sm text-slate-500">
                {{ item.task_count }} 个任务 | 平均难度
                {{ item.avg_difficulty }}
              </p>
            </div>
            <p class="text-lg font-bold text-indigo-600">
              {{ item.total_score }}
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
