<script setup lang="ts">
/**
 * 应用根组件
 */
import { onMounted } from "vue";
import { useAuthStore } from "./stores/auth";

const authStore = useAuthStore();

// 初始化时获取当前用户信息
onMounted(async () => {
  if (authStore.token) {
    await authStore.fetchCurrentUser();
  }
});
</script>

<template>
  <router-view />
</template>
