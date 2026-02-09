<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  node: any;
  depth: number;
  expandedKeys: Set<string>;
}>();

const emit = defineEmits([
  "toggle-expand",
  "add-dept",
  "add-pos",
  "edit-dept",
  "delete-dept",
]);

const isExpanded = computed(() => props.expandedKeys.has(props.node.id));

function handleToggle() {
  emit("toggle-expand", props.node);
}

// 计算缩进样式，虽然是递归，但为了视觉层级，我们可以利用 padding
// 或者直接嵌套 div。这里使用嵌套 div 结构 naturally indentation.
</script>

<template>
  <div class="tree-item">
    <!-- 节点内容 -->
    <div
      class="flex items-center gap-2 py-2 px-2 hover:bg-slate-50 rounded-lg group transition-colors"
    >
      <!-- 展开/折叠按钮 (仅部门) -->
      <button
        v-if="node.type === 'department'"
        @click="handleToggle"
        class="text-slate-400 hover:text-slate-600 w-6 h-6 flex items-center justify-center rounded hover:bg-slate-200 transition-colors"
      >
        <span v-if="node.children && node.children.length > 0">
          {{ isExpanded ? "▼" : "▶" }}
        </span>
        <span v-else>•</span>
      </button>

      <!-- 图标 -->
      <span v-if="node.type === 'organization'" class="text-xl">🏢</span>
      <span v-else-if="node.type === 'department'" class="text-slate-500"
        >📁</span
      >
      <span v-else-if="node.type === 'position'" class="text-slate-500"
        >👤</span
      >

      <!-- 名称 -->
      <span
        class="font-medium"
        :class="
          node.type === 'organization'
            ? 'text-lg text-slate-800'
            : node.type === 'department'
            ? 'text-slate-700'
            : 'text-sm text-slate-600'
        "
      >
        {{ node.name }}
      </span>

      <!-- 标签/额外信息 -->
      <span
        v-if="node.code"
        class="text-[10px] px-1.5 py-0.5 bg-slate-100 text-slate-500 rounded border border-slate-200"
      >
        {{ node.code }}
      </span>
      <span
        v-if="node.type === 'position' && node.can_assign"
        class="text-[10px] px-1.5 py-0.5 bg-green-50 text-green-600 rounded border border-green-100"
      >
        主管
      </span>

      <!-- 操作按钮 (Hover 显示) -->
      <div
        class="flex items-center gap-2 ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
      >
        <template v-if="node.type === 'organization'">
          <button
            @click="$emit('add-dept', node, node.id)"
            class="text-xs text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded"
          >
            + 部门
          </button>
        </template>

        <template v-if="node.type === 'department'">
          <button
            @click="$emit('add-dept', node, node.organization_id || '')"
            class="text-xs text-indigo-600 hover:bg-indigo-50 px-2 py-1 rounded"
          >
            + 子部门
          </button>
          <button
            @click="$emit('add-pos', node)"
            class="text-xs text-purple-600 hover:bg-purple-50 px-2 py-1 rounded"
          >
            + 岗位
          </button>
          <button
            @click="$emit('edit-dept', node)"
            class="text-xs text-slate-500 hover:bg-slate-100 px-2 py-1 rounded"
          >
            编辑
          </button>
          <button
            @click="$emit('delete-dept', node.id)"
            class="text-xs text-red-500 hover:bg-red-50 px-2 py-1 rounded"
          >
            删除
          </button>
        </template>
      </div>
    </div>

    <!-- 子节点 (递归渲染) -->
    <div
      v-if="
        (node.type === 'organization' ||
          (node.type === 'department' && isExpanded)) &&
        node.children &&
        node.children.length > 0
      "
      class="pl-6 border-l border-slate-100 ml-4"
    >
      <OrgTreeItem
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="depth + 1"
        :expanded-keys="expandedKeys"
        @toggle-expand="(n) => $emit('toggle-expand', n)"
        @add-dept="(n, oid) => $emit('add-dept', n, oid)"
        @add-pos="(n) => $emit('add-pos', n)"
        @edit-dept="(n) => $emit('edit-dept', n)"
        @delete-dept="(id) => $emit('delete-dept', id)"
      />
    </div>
  </div>
</template>
