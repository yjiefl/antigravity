<script setup lang="ts">
/**
 * 登录页面
 */
import { ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// 表单数据
const username = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");

// 登录处理
async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = "请输入用户名和密码";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    await authStore.login(username.value, password.value);

    // 跳转到之前的页面或仪表盘
    const redirect = route.query.redirect as string;
    router.push(redirect || "/");
  } catch (e: any) {
    error.value = e.response?.data?.detail || "登录失败，请检查用户名和密码";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div
    class="min-h-screen bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center p-4"
  >
    <div class="w-full max-w-md">
      <!-- 登录卡片 -->
      <div class="bg-white rounded-2xl shadow-xl p-8">
        <!-- Logo -->
        <div class="text-center mb-8">
          <div
            class="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4"
          >
            <span class="text-3xl">📋</span>
          </div>
          <h1 class="text-2xl font-bold text-slate-800">计划管理系统</h1>
          <p class="text-slate-500 mt-2">请登录您的账户</p>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- 用户名 -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >用户名</label
            >
            <input
              v-model="username"
              type="text"
              placeholder="请输入用户名"
              class="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-colors"
            />
          </div>

          <!-- 密码 -->
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-2"
              >密码</label
            >
            <input
              v-model="password"
              type="password"
              placeholder="请输入密码"
              class="w-full px-4 py-3 rounded-lg border border-slate-200 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition-colors"
            />
          </div>

          <!-- 错误提示 -->
          <div
            v-if="error"
            class="text-red-500 text-sm text-center bg-red-50 py-2 rounded-lg"
          >
            {{ error }}
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ loading ? "登录中..." : "登录" }}
          </button>
        </form>

        <!-- 演示账户提示 -->
        <div class="mt-6 text-center text-sm text-slate-500">
          <p>演示账户: admin / admin123</p>
        </div>
      </div>

      <!-- 版权信息 -->
      <p class="text-center text-white/70 text-sm mt-6">
        © 2026 计划管理系统 v1.0
      </p>
    </div>
  </div>
</template>
