<script setup lang="ts">
/**
 * 批量导入任务页面
 */
import { ref } from "vue";
import api from "../api";

const file = ref<File | null>(null);
const importing = ref(false);
const result = ref<any>(null);
const error = ref("");

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement;
  const selectedFile = target.files?.[0];
  if (selectedFile) {
    file.value = selectedFile;
    result.value = null;
    error.value = "";
  }
}

async function downloadTemplate() {
  try {
    const res = await api.get("/api/batch/template", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "task_import_template.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (e) {
    alert("下载模板失败");
  }
}

async function importTasks() {
  if (!file.value) {
    error.value = "请先选择文件";
    return;
  }

  importing.value = true;
  error.value = "";
  result.value = null;

  try {
    const formData = new FormData();
    formData.append("file", file.value);

    const res = await api.post("/api/batch/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    result.value = res.data;
    if (result.value.success_count > 0) {
      alert(`导入完成！成功: ${result.value.success_count}, 失败: ${result.value.error_count}`);
    } else {
      alert("导入失败，请查看详情报告");
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail || "导入失败";
  } finally {
    importing.value = false;
  }
}

function resetForm() {
  file.value = null;
  result.value = null;
  error.value = "";
  const input = document.getElementById("fileInput") as HTMLInputElement;
  if (input) input.value = "";
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-slate-800">📥 批量导入任务</h1>
    </div>

    <!-- 说明卡片 -->
    <div class="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-6 rounded-xl">
      <h2 class="text-lg font-bold mb-2">📋 导入说明</h2>
      <ul class="space-y-1 text-sm opacity-90">
        <li>• 支持 <b>CSV</b> 和 <b>Excel (.xlsx)</b> 格式</li>
        <li>• 第一行必须是表头，从第二行开始为数据</li>
        <li>• <b>任务标题</b> 为必填项</li>
        <li>• 日期格式：YYYY-MM-DD（如 2026-02-15）</li>
        <li>• 负责人/实施人填写 <b>用户名</b>（非姓名）</li>
      </ul>
      <button @click="downloadTemplate" class="mt-4 px-4 py-2 bg-white text-indigo-600 rounded-lg font-bold hover:bg-indigo-50 transition-colors">
        ⬇️ 下载导入模板
      </button>
    </div>

    <!-- 上传区域 -->
    <div class="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
      <div class="border-2 border-dashed border-slate-200 rounded-xl p-8 text-center hover:border-indigo-400 transition-colors">
        <div class="text-4xl mb-4">📁</div>
        <p class="text-slate-600 mb-4">选择 CSV 或 Excel 文件</p>
        <input
          id="fileInput"
          type="file"
          accept=".csv,.xlsx"
          @change="onFileChange"
          class="hidden"
        />
        <label for="fileInput" class="btn btn-secondary cursor-pointer">
          选择文件
        </label>
        <p v-if="file" class="mt-4 text-indigo-600 font-bold">
          已选择: {{ file.name }}
        </p>
      </div>

      <div class="flex gap-4 mt-6">
        <button
          @click="importTasks"
          :disabled="!file || importing"
          class="btn btn-primary flex-1"
          :class="{ 'opacity-50 cursor-not-allowed': !file || importing }"
        >
          {{ importing ? "导入中..." : "🚀 开始导入" }}
        </button>
        <button @click="resetForm" class="btn btn-secondary">
          重置
        </button>
      </div>

      <p v-if="error" class="mt-4 text-red-600 font-bold">❌ {{ error }}</p>
    </div>

    <!-- 导入结果 -->
    <div v-if="result" class="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
      <h3 class="text-lg font-bold mb-4">📊 导入结果</h3>
      
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-slate-50 p-4 rounded-lg text-center">
          <div class="text-3xl font-bold text-slate-700">{{ result.total }}</div>
          <div class="text-sm text-slate-500">总记录数</div>
        </div>
        <div class="bg-green-50 p-4 rounded-lg text-center">
          <div class="text-3xl font-bold text-green-600">{{ result.success_count }}</div>
          <div class="text-sm text-slate-500">成功</div>
        </div>
        <div class="bg-red-50 p-4 rounded-lg text-center">
          <div class="text-3xl font-bold text-red-600">{{ result.error_count }}</div>
          <div class="text-sm text-slate-500">失败</div>
        </div>
      </div>

      <!-- 详细结果 -->
      <div class="max-h-80 overflow-y-auto">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 sticky top-0">
            <tr>
              <th class="px-4 py-2 text-left">行号</th>
              <th class="px-4 py-2 text-left">任务标题</th>
              <th class="px-4 py-2 text-left">状态</th>
              <th class="px-4 py-2 text-left">说明</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="item in result.details" :key="item.row" class="hover:bg-slate-50">
              <td class="px-4 py-2">{{ item.row }}</td>
              <td class="px-4 py-2 font-medium">{{ item.title || '-' }}</td>
              <td class="px-4 py-2">
                <span v-if="item.status === 'success'" class="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-bold">成功</span>
                <span v-else class="px-2 py-0.5 bg-red-100 text-red-700 rounded text-xs font-bold">失败</span>
              </td>
              <td class="px-4 py-2 text-slate-500">
                {{ item.status === 'success' ? item.task_id : item.message }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
