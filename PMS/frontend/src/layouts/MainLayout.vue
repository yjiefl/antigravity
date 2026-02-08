<script setup lang="ts">
/**
 * 主布局组件
 *
 * PC 端侧边栏导航 + 移动端底部导航
 */
import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// 侧边栏展开状态
const sidebarOpen = ref(true);

// 导航菜单
const navItems = [
  { name: "仪表盘", path: "/", icon: "📊" },
  { name: "任务管理", path: "/tasks", icon: "📋" },
  { name: "绩效统计", path: "/kpi", icon: "📈" },
  {
    name: "申诉审核",
    path: "/appeals/review",
    icon: "⚖️",
    roles: ["admin", "manager"],
  },
  { name: "帮助说明", path: "/help", icon: "❓" },
];

// 过滤后的导航菜单
const filteredNavItems = computed(() => {
  return navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(authStore.user?.role || "");
  });
});

// 当前路由
const currentPath = computed(() => route.path);

// 登出
function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>

<template>
  <div class="min-h-screen bg-indigo-50/30 flex">
    <!-- PC 端侧边栏 -->
    <aside
      class="hidden md:flex flex-col w-64 glass-effect border-r border-white/20 shadow-xl transition-all duration-300"
    >
      <!-- Logo -->
      <div
        class="p-6 border-b border-indigo-100/30 bg-white/10 backdrop-blur-md"
      >
        <h1 class="text-xl font-bold tracking-tight text-indigo-700">
          计划管理系统
        </h1>
      </div>

      <!-- 导航菜单 -->
      <nav class="flex-1 p-4 space-y-2 mt-4">
        <router-link
          v-for="item in filteredNavItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 group relative"
          :class="
            currentPath === item.path
              ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
              : 'text-slate-600 hover:bg-white/60 hover:text-indigo-600'
          "
        >
          <span
            class="text-xl transition-transform duration-200 group-hover:scale-110"
            >{{ item.icon }}</span
          >
          <span class="font-semibold tracking-wide">{{ item.name }}</span>
          <div
            v-if="currentPath === item.path && !sidebarOpen"
            class="absolute left-full ml-2 px-2 py-1 bg-indigo-700 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity"
          >
            {{ item.name }}
          </div>
        </router-link>
      </nav>

      <!-- 用户信息 -->
      <div class="p-4 border-t border-indigo-100/30 bg-white/5">
        <div
          class="flex items-center gap-3 p-2 rounded-xl transition-colors hover:bg-white/40"
        >
          <div
            class="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center text-white font-bold shadow-md shadow-indigo-100"
          >
            {{ authStore.user?.realName?.charAt(0) || "?" }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-bold text-slate-800 truncate text-sm">
              {{ authStore.user?.realName }}
            </p>
            <p
              class="text-[10px] font-bold uppercase tracking-widest text-indigo-500 opacity-60"
            >
              {{ authStore.user?.role }}
            </p>
          </div>
          <button
            @click="handleLogout"
            class="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
            title="登出"
          >
            🚪
          </button>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 flex flex-col min-h-screen">
      <!-- 顶部栏 -->
      <header
        class="glass-effect sticky top-0 z-40 px-8 py-4 flex items-center justify-between border-b border-white/20 shadow-sm"
      >
        <div class="md:hidden"></div>
        <h2 class="text-lg font-bold text-indigo-900 md:hidden">
          计划管理系统
        </h2>
        <div class="flex items-center gap-6">
          <div
            class="flex items-center gap-2 px-3 py-1.5 bg-white/40 rounded-full border border-white/60 shadow-inner"
          >
            <span class="text-xs font-bold text-indigo-600">{{
              new Date().toLocaleDateString("zh-CN", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
              })
            }}</span>
          </div>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="flex-1 p-6 overflow-auto">
        <router-view />
      </div>
    </main>

    <!-- 移动端底部导航 -->
    <nav
      class="md:hidden fixed bottom-0 left-0 right-0 glass-effect border-t border-white/20 flex justify-around py-2 z-40 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]"
    >
      <router-link
        v-for="item in filteredNavItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center py-2 px-4 transition-all duration-200"
        :class="
          currentPath === item.path ? 'text-indigo-600' : 'text-slate-500'
        "
      >
        <span
          class="text-xl"
          :class="{ 'scale-110': currentPath === item.path }"
          >{{ item.icon }}</span
        >
        <span class="text-[10px] mt-1 font-bold">{{ item.name }}</span>
      </router-link>
    </nav>
  </div>
</template>
