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
  { name: "帮助说明", path: "/help", icon: "❓" },
];

// 当前路由
const currentPath = computed(() => route.path);

// 登出
function handleLogout() {
  authStore.logout();
  router.push("/login");
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex">
    <!-- PC 端侧边栏 -->
    <aside
      class="hidden md:flex flex-col w-64 bg-white border-r border-slate-200"
      :class="{ 'w-20': !sidebarOpen }"
    >
      <!-- Logo -->
      <div class="p-4 border-b border-slate-200">
        <h1 class="text-xl font-bold text-indigo-600" v-if="sidebarOpen">
          计划管理系统
        </h1>
        <span class="text-2xl" v-else>📋</span>
      </div>

      <!-- 导航菜单 -->
      <nav class="flex-1 p-4 space-y-2">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-4 py-3 rounded-lg transition-colors"
          :class="
            currentPath === item.path
              ? 'bg-indigo-50 text-indigo-600'
              : 'text-slate-600 hover:bg-slate-50'
          "
        >
          <span class="text-xl">{{ item.icon }}</span>
          <span v-if="sidebarOpen">{{ item.name }}</span>
        </router-link>
      </nav>

      <!-- 用户信息 -->
      <div class="p-4 border-t border-slate-200">
        <div class="flex items-center gap-3" v-if="sidebarOpen">
          <div
            class="w-10 h-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold"
          >
            {{ authStore.user?.realName?.charAt(0) || "?" }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="font-medium text-slate-800 truncate">
              {{ authStore.user?.realName }}
            </p>
            <p class="text-sm text-slate-500">{{ authStore.user?.role }}</p>
          </div>
          <button
            @click="handleLogout"
            class="text-slate-400 hover:text-red-500"
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
        class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between"
      >
        <button
          @click="sidebarOpen = !sidebarOpen"
          class="hidden md:block text-slate-500 hover:text-slate-700"
        >
          ☰
        </button>
        <h2 class="text-lg font-semibold text-slate-800 md:hidden">
          计划管理系统
        </h2>
        <div class="flex items-center gap-4">
          <span class="text-sm text-slate-500">{{
            new Date().toLocaleDateString("zh-CN")
          }}</span>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="flex-1 p-6 overflow-auto">
        <router-view />
      </div>
    </main>

    <!-- 移动端底部导航 -->
    <nav
      class="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 flex justify-around py-2"
    >
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="flex flex-col items-center py-2 px-4"
        :class="
          currentPath === item.path ? 'text-indigo-600' : 'text-slate-500'
        "
      >
        <span class="text-xl">{{ item.icon }}</span>
        <span class="text-xs mt-1">{{ item.name }}</span>
      </router-link>
    </nav>
  </div>
</template>
