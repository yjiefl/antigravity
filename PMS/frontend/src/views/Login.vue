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
    class="min-h-screen bg-indigo-50 flex items-center justify-center p-6 relative overflow-hidden"
  >
    <!-- 装饰性背景 -->
    <div
      class="absolute -top-24 -left-24 w-96 h-96 bg-indigo-200/50 rounded-full blur-3xl"
    ></div>
    <div
      class="absolute -bottom-24 -right-24 w-96 h-96 bg-purple-200/50 rounded-full blur-3xl"
    ></div>

    <div class="w-full max-w-md relative z-10">
      <!-- 登录卡片 -->
      <div class="glass-card p-10 backdrop-blur-2xl border-white/40 shadow-2xl">
        <!-- Logo -->
        <div class="text-center mb-10">
          <div
            class="w-20 h-20 bg-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-xl shadow-indigo-100 group hover:rotate-6 transition-transform"
          >
            <span class="text-4xl">📋</span>
          </div>
          <h1 class="text-3xl font-black text-indigo-950 tracking-tighter">
            计划管理系统
          </h1>
          <p
            class="text-slate-400 mt-2 font-bold uppercase tracking-widest text-[10px]"
          >
            身份认证网关
          </p>
        </div>

        <!-- 登录表单 -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <!-- 用户名 -->
          <div class="space-y-2">
            <label
              class="block text-[10px] font-black text-indigo-900/40 uppercase tracking-widest ml-1"
              >用户名</label
            >
            <div class="relative group">
              <span
                class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-indigo-600 transition-colors"
                >👤</span
              >
              <input
                v-model="username"
                type="text"
                placeholder="请输入用户名"
                class="w-full pl-11 pr-4 py-3.5 bg-white/50 border border-slate-200 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all outline-none font-semibold text-slate-700 placeholder:text-slate-300 placeholder:italic"
              />
            </div>
          </div>

          <!-- 密码 -->
          <div class="space-y-2">
            <label
              class="block text-[10px] font-black text-indigo-900/40 uppercase tracking-widest ml-1"
              >密码</label
            >
            <div class="relative group">
              <span
                class="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300 group-focus-within:text-indigo-600 transition-colors"
                >🔒</span
              >
              <input
                v-model="password"
                type="password"
                placeholder="••••••••"
                class="w-full pl-11 pr-4 py-3.5 bg-white/50 border border-slate-200 rounded-2xl focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 transition-all outline-none font-semibold text-slate-700 placeholder:text-slate-300"
              />
            </div>
          </div>

          <!-- 错误提示 -->
          <div
            v-if="error"
            class="text-red-500 text-[10px] font-black text-center bg-red-50/50 py-2.5 rounded-xl border border-red-100 uppercase tracking-widest animate-in fade-in slide-in-from-top-2"
          >
            ⚠️ {{ error }}
          </div>

          <!-- 登录按钮 -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-4 bg-indigo-600 text-white font-black rounded-2xl hover:bg-indigo-700 transition-all shadow-xl shadow-indigo-100 flex items-center justify-center gap-2 group disabled:opacity-50 disabled:cursor-not-allowed active:scale-[0.98]"
          >
            <span
              v-if="loading"
              class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"
            ></span>
            <span v-else class="uppercase tracking-widest text-sm italic">{{
              loading ? "认证中..." : "立即登录"
            }}</span>
          </button>
        </form>

        <!-- 演示账户提示 -->
        <div class="mt-8 pt-8 border-t border-slate-100/50 text-center">
          <p
            class="text-[10px] font-bold text-slate-400 uppercase tracking-widest"
          >
            演示账户: <span class="text-indigo-600">admin</span> /
            <span class="text-indigo-600">admin123</span>
          </p>
        </div>
      </div>

      <!-- 版权信息 -->
      <p
        class="text-center text-slate-400 text-[10px] font-black uppercase tracking-widest mt-8 flex items-center justify-center gap-2"
      >
        <span class="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
        © 2026 计划管理系统 v1.0 • 追求卓越，成就效率
      </p>
    </div>
  </div>
</template>
