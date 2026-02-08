<script setup lang="ts">
/**
 * 绩效统计页面
 */
import { ref, onMounted } from "vue";
import { useAuthStore } from "../stores/auth";
import api from "../api";
import AppealModal from "../components/AppealModal.vue";

const authStore = useAuthStore();

const personalKpi = ref<any>(null);
const ranking = ref<any[]>([]);
const penaltyCards = ref<any[]>([]);
const loading = ref(true);

// 申诉弹窗控制
const showAppealModal = ref(false);
const selectedCard = ref<any>(null);

function openAppealModal(card: any) {
  selectedCard.value = card;
  showAppealModal.value = true;
}

function handleAppealSuccess() {
  showAppealModal.value = false;
  loadKpi(); // 重新加载数据以更新状态
}

async function loadKpi() {
  loading.value = true;
  try {
    const userId = authStore.user?.id;
    if (userId) {
      const [kpiRes, rankRes, cardsRes] = await Promise.all([
        api.get(`/api/kpi/personal/${userId}`),
        api.get("/api/kpi/ranking", { params: { limit: 10 } }),
        api.get("/api/appeals/my-cards"),
      ]);
      personalKpi.value = kpiRes.data || {};
      ranking.value = rankRes.data || [];
      penaltyCards.value = cardsRes.data || [];
    }
  } catch (e) {
    console.error("加载 KPI 失败", e);
  } finally {
    loading.value = false;
  }
}

function formatDate(dateStr: string) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getAppealStatusText(status: string) {
  const map: Record<string, string> = {
    pending: "可申诉",
    reviewing: "审核中",
    approved: "申诉通过",
    rejected: "驳回",
  };
  return map[status] || "未知";
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


      <div class="grid lg:grid-cols-3 gap-8">
        <!-- 罚单历史与申诉 -->
        <div class="lg:col-span-2 glass-card flex flex-col">
          <div class="p-6 border-b border-white/20 bg-white/30 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800">惩罚性考核记录</h2>
            <span class="text-[10px] font-bold bg-slate-100 text-slate-500 px-2 py-1 rounded uppercase tracking-wider">最近触发</span>
          </div>
          <div class="p-6 flex-1">
            <div
              v-if="penaltyCards.length === 0"
              class="text-slate-400 text-center py-12 flex flex-col items-center gap-3"
            >
              <div class="text-4xl">🍃</div>
              <p class="font-bold tracking-widest uppercase text-xs">暂无考核记录，请保持</p>
            </div>
            <div v-else class="space-y-4">
              <div
                v-for="card in penaltyCards"
                :key="card.id"
                class="flex flex-col sm:flex-row sm:items-center gap-4 p-4 rounded-2xl border transition-all duration-300 group"
                :class="card.card_type === 'red' ? 'bg-red-50/40 border-red-100/50 hover:bg-red-50/60 shadow-sm hover:shadow-red-100' : 'bg-yellow-50/40 border-yellow-100/50 hover:bg-yellow-50/60 shadow-sm hover:shadow-yellow-100'"
              >
                <div
                  class="w-14 h-14 rounded-xl flex items-center justify-center text-3xl shadow-inner group-hover:scale-110 transition-transform"
                  :class="card.card_type === 'red' ? 'bg-red-100 text-red-500' : 'bg-yellow-100 text-yellow-600'"
                >
                  {{ card.card_type === 'red' ? '🟥' : '🟨' }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex flex-wrap items-center gap-2 mb-2">
                    <span class="font-bold text-slate-800 text-base">{{ card.task_title }}</span>
                    <span
                      class="text-[10px] font-black px-2 py-1 rounded uppercase tracking-tighter"
                      :class="card.card_type === 'red' ? 'bg-red-500 text-white' : 'bg-yellow-400 text-slate-800'"
                    >
                      {{ card.card_type === 'red' ? '红牌考核' : '黄牌考核' }}
                    </span>
                    <span
                      v-if="card.penalty_score > 0"
                      class="text-sm font-black text-red-600 flex items-center gap-1"
                    >
                      <span class="text-[10px]">扣分</span> -{{ card.penalty_score }}
                    </span>
                    <span
                      v-else-if="card.card_type === 'red'"
                      class="text-xs font-bold text-green-600 bg-green-50 px-2 py-0.5 rounded-full border border-green-100"
                    >
                      ✓ 已撤销
                    </span>
                  </div>
                  <p class="text-xs font-medium text-slate-500 line-clamp-2 leading-relaxed italic">
                    "{{ card.reason_analysis }}"
                  </p>
                  <p class="text-[10px] font-bold text-slate-400 mt-2 uppercase tracking-widest flex items-center gap-1">
                    🕒 触发时间: {{ formatDate(card.triggered_at) }}
                  </p>
                </div>

                <!-- 申诉操作 -->
                <div
                  v-if="card.card_type === 'red'"
                  class="flex items-center gap-3 mt-2 sm:mt-0"
                >
                  <span
                    v-if="card.appeal_status && card.appeal_status !== 'pending'"
                    class="text-xs font-black uppercase tracking-widest px-3 py-1.5 rounded-full shadow-inner"
                    :class="{
                      'bg-amber-100 text-amber-700': card.appeal_status === 'reviewing',
                      'bg-green-100 text-green-700': card.appeal_status === 'approved',
                      'bg-red-100 text-red-700': card.appeal_status === 'rejected',
                    }"
                  >
                    {{ getAppealStatusText(card.appeal_status) }}
                  </span>
                  <button
                    v-if="!card.appeal_status || card.appeal_status === 'pending'"
                    class="btn btn-secondary !py-2 !text-xs !rounded-full border-red-200 text-red-600 hover:bg-red-600 hover:text-white hover:border-red-600 shadow-sm"
                    @click="openAppealModal(card)"
                  >
                    🚀 发起申诉
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 排行榜 -->
        <div class="glass-card flex flex-col">
          <div class="p-6 border-b border-white/20 bg-white/30 flex items-center justify-between">
            <h2 class="text-lg font-bold text-slate-800">🏆 难度贡献榜</h2>
            <span class="text-xs font-bold text-indigo-400">Top 10</span>
          </div>
          <div class="p-6 flex-1">
            <div
              v-if="ranking.length === 0"
              class="text-slate-400 text-center py-12"
            >
              暂无数据
            </div>
            <div v-else class="space-y-4">
              <div
                v-for="(item, index) in ranking"
                :key="item.user_id"
                class="flex items-center gap-4 p-4 rounded-2xl transition-all duration-300"
                :class="index === 0 ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-100 scale-105' : 'bg-white/40 hover:bg-white/80'"
              >
                <div
                  class="w-8 h-8 rounded-lg flex items-center justify-center font-black italic text-lg shadow-sm"
                  :class="{
                    'bg-white/20 text-white': index === 0,
                    'bg-slate-200 text-slate-600': index === 1,
                    'bg-amber-100 text-amber-600': index === 2,
                    'bg-slate-50 text-slate-300': index > 2,
                  }"
                >
                  {{ index + 1 }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="font-bold truncate" :class="index === 0 ? 'text-white' : 'text-slate-800'">{{ item.real_name }}</p>
                  <p class="text-[10px] font-bold uppercase tracking-widest opacity-60">
                    {{ item.task_count }} 任务 | 难度 {{ item.avg_difficulty }}
                  </p>
                </div>
                <p class="text-xl font-black tabular-nums" :class="index === 0 ? 'text-white' : 'text-indigo-600'">
                  {{ item.total_score }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>

    <!-- 申诉弹窗 -->
    <AppealModal
      v-if="showAppealModal"
      :card="selectedCard"
      @close="showAppealModal = false"
      @success="handleAppealSuccess"
    />
  </div>
</template>
