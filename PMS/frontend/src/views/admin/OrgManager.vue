<script setup lang="ts">
/**
 * 组织架构管理
 *
 * 展示公司-部门-岗位树形结构，支持增删改查
 */
import { ref, onMounted, computed } from "vue";
import api from "../../api"; // Adjust import path based on location
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
const loading = ref(true);
const treeData = ref<any[]>([]);
const expandedKeys = ref<Set<string>>(new Set());

// 模态框控制
const showOrgModal = ref(false);
const showDeptModal = ref(false);
const showPosModal = ref(false);

// 表单数据
const orgForm = ref({ id: "", name: "", code: "" });
const deptForm = ref({
  id: "",
  name: "",
  code: "",
  parent_id: "",
  organization_id: "",
});
const posForm = ref({
  id: "",
  name: "",
  code: "",
  department_id: "",
  can_assign_task: false,
  can_transfer_task: false,
});

// 当前选中的节点（用于添加子节点）
const currentNode = ref<any>(null);
const isEdit = ref(false);

// 加载组织架构树
async function loadTree() {
  loading.value = true;
  try {
    const res = await api.get("/api/org/tree");
    treeData.value = res.data;
    // 默认展开所有
    expandAll(treeData.value);
  } catch (e) {
    console.error("加载组织架构失败", e);
  } finally {
    loading.value = false;
  }
}

function expandAll(nodes: any[]) {
  nodes.forEach((node) => {
    expandedKeys.value.add(node.id);
    if (node.children) {
      expandAll(node.children);
    }
  });
}

function toggleExpand(node: any) {
  if (expandedKeys.value.has(node.id)) {
    expandedKeys.value.delete(node.id);
  } else {
    expandedKeys.value.add(node.id);
  }
}

// === 公司操作 ===
function openAddOrg() {
  isEdit.value = false;
  orgForm.value = { id: "", name: "", code: "" };
  showOrgModal.value = true;
}

async function submitOrg() {
  try {
    if (isEdit.value) {
      // API expected to be implemented if editing org is needed, currently only create in plan
      alert("编辑功能暂未开放");
    } else {
      await api.post("/api/org/organizations", orgForm.value);
    }
    showOrgModal.value = false;
    await loadTree();
  } catch (e) {
    alert("操作失败");
  }
}

// === 部门操作 ===
function openAddDept(parent: any, orgId: string) {
  isEdit.value = false;
  currentNode.value = parent;
  deptForm.value = {
    id: "",
    name: "",
    code: "",
    parent_id: parent.type === "department" ? parent.id : null,
    organization_id: orgId,
  };
  showDeptModal.value = true;
}

function openEditDept(dept: any) {
  isEdit.value = true;
  deptForm.value = { ...dept, organization_id: "" }; // org_id might need to be passed or found
  showDeptModal.value = true;
}

async function submitDept() {
  try {
    if (isEdit.value) {
      await api.put(
        `/api/org/departments/${deptForm.value.id}`,
        deptForm.value,
      );
    } else {
      await api.post("/api/org/departments", deptForm.value);
    }
    showDeptModal.value = false;
    await loadTree();
  } catch (e) {
    alert("操作失败");
  }
}

async function deleteDept(id: string) {
  if (!confirm("确认删除该部门？如果有子部门或人员将无法删除。")) return;
  try {
    await api.delete(`/api/org/departments/${id}`);
    await loadTree();
  } catch (e: any) {
    alert(e.response?.data?.detail || "删除失败");
  }
}

// === 岗位操作 ===
function openAddPos(dept: any) {
  isEdit.value = false;
  currentNode.value = dept;
  posForm.value = {
    id: "",
    name: "",
    code: "",
    department_id: dept.id,
    can_assign_task: false,
    can_transfer_task: false,
  };
  showPosModal.value = true;
}

async function submitPos() {
  try {
    if (isEdit.value) {
      // API for position update if needed
    } else {
      await api.post("/api/org/positions", posForm.value);
    }
    showPosModal.value = false;
    await loadTree();
  } catch (e) {
    alert("操作失败");
  }
}

onMounted(() => {
  loadTree();
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-slate-800">🏢 组织架构管理</h1>
      <button
        @click="openAddOrg"
        class="btn btn-primary"
        v-if="authStore.isAdmin"
      >
        + 新增公司
      </button>
    </div>

    <div v-if="loading" class="text-center py-12 text-slate-400">加载中...</div>

    <div
      v-else
      class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden"
    >
      <!-- 递归组件或简单列表展示 -->
      <div class="p-6">
        <template v-for="org in treeData" :key="org.id">
          <div class="mb-6 last:mb-0">
            <div class="flex items-center gap-2 mb-2 group">
              <span class="text-xl">🏢</span>
              <span class="font-bold text-lg text-slate-800">{{
                org.name
              }}</span>
              <span class="text-xs px-2 py-0.5 bg-slate-100 rounded">{{
                org.code
              }}</span>
              <button
                @click="openAddDept(org, org.id)"
                class="text-xs text-indigo-500 opacity-0 group-hover:opacity-100 hover:underline"
              >
                + 部门
              </button>
            </div>

            <div class="pl-6 border-l-2 border-slate-100 space-y-3">
              <template v-for="dept in org.children" :key="dept.id">
                <div class="group">
                  <div class="flex items-center gap-2 py-1">
                    <button
                      @click="toggleExpand(dept)"
                      class="text-slate-400 hover:text-slate-600 w-4"
                    >
                      {{
                        dept.children && dept.children.length > 0
                          ? expandedKeys.has(dept.id)
                            ? "▼"
                            : "▶"
                          : "•"
                      }}
                    </button>
                    <span class="font-medium text-slate-700">{{
                      dept.name
                    }}</span>

                    <div
                      class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity ml-4"
                    >
                      <button
                        @click="openAddDept(dept, org.id)"
                        class="text-xs text-indigo-600 hover:underline"
                      >
                        + 子部门
                      </button>
                      <button
                        @click="openAddPos(dept)"
                        class="text-xs text-purple-600 hover:underline"
                      >
                        + 岗位
                      </button>
                      <button
                        @click="openEditDept(dept)"
                        class="text-xs text-slate-500 hover:underline"
                      >
                        编辑
                      </button>
                      <button
                        @click="deleteDept(dept.id)"
                        class="text-xs text-red-500 hover:underline"
                      >
                        删除
                      </button>
                    </div>
                  </div>

                  <div
                    v-if="expandedKeys.has(dept.id)"
                    class="pl-6 border-l border-slate-100 mt-1"
                  >
                    <!-- 子部门和岗位渲染逻辑 (需递归) -->
                    <!-- 这里简单处理一层子部门和岗位用于演示，实际建议封装 TreeItem 组件 -->
                    <div
                      v-for="child in dept.children"
                      :key="child.id"
                      class="py-1"
                    >
                      <div
                        v-if="child.type === 'department'"
                        class="flex items-center gap-2"
                      >
                        <span class="text-slate-400">↳ 📁</span>
                        <span>{{ child.name }}</span>
                        <button
                          @click="deleteDept(child.id)"
                          class="text-xs text-red-500 ml-2 opacity-0 hover:opacity-100 group-hover:block hidden"
                        >
                          删除
                        </button>
                      </div>
                      <div
                        v-else-if="child.type === 'position'"
                        class="flex items-center gap-2"
                      >
                        <span class="text-slate-400">↳ 👤</span>
                        <span class="text-sm text-slate-600">{{
                          child.name
                        }}</span>
                        <span
                          v-if="child.can_assign"
                          class="text-[10px] bg-green-100 text-green-700 px-1 rounded"
                          >主管权限</span
                        >
                      </div>
                    </div>
                    <div
                      v-if="!dept.children || dept.children.length === 0"
                      class="text-xs text-slate-400 py-1"
                    >
                      (空)
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- 公司模态框 -->
    <div
      v-if="showOrgModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-xl p-6 w-96">
        <h3 class="font-bold mb-4">{{ isEdit ? "编辑" : "新增" }}公司</h3>
        <div class="space-y-4">
          <input
            v-model="orgForm.name"
            placeholder="公司名称"
            class="input w-full"
          />
          <input
            v-model="orgForm.code"
            placeholder="编码 (可选)"
            class="input w-full"
          />
          <div class="flex gap-2">
            <button
              @click="showOrgModal = false"
              class="btn btn-secondary flex-1"
            >
              取消
            </button>
            <button @click="submitOrg" class="btn btn-primary flex-1">
              保存
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 部门模态框 -->
    <div
      v-if="showDeptModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-xl p-6 w-96">
        <h3 class="font-bold mb-4">{{ isEdit ? "编辑" : "新增" }}部门</h3>
        <div class="space-y-4">
          <div v-if="currentNode" class="text-sm text-slate-500">
            上级: {{ currentNode.name }}
          </div>
          <input
            v-model="deptForm.name"
            placeholder="部门名称"
            class="input w-full"
          />
          <input
            v-model="deptForm.code"
            placeholder="编码 (可选)"
            class="input w-full"
          />
          <div class="flex gap-2">
            <button
              @click="showDeptModal = false"
              class="btn btn-secondary flex-1"
            >
              取消
            </button>
            <button @click="submitDept" class="btn btn-primary flex-1">
              保存
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 岗位模态框 -->
    <div
      v-if="showPosModal"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-xl p-6 w-96">
        <h3 class="font-bold mb-4">新增岗位</h3>
        <div class="space-y-4">
          <div v-if="currentNode" class="text-sm text-slate-500">
            所属部门: {{ currentNode.name }}
          </div>
          <input
            v-model="posForm.name"
            placeholder="岗位名称"
            class="input w-full"
          />
          <input
            v-model="posForm.code"
            placeholder="编码 (可选)"
            class="input w-full"
          />
          <div class="flex items-center gap-2">
            <input
              type="checkbox"
              v-model="posForm.can_assign_task"
              id="can_assign"
            />
            <label for="can_assign" class="text-sm">允许分配任务（主管）</label>
          </div>
          <div class="flex gap-2">
            <button
              @click="showPosModal = false"
              class="btn btn-secondary flex-1"
            >
              取消
            </button>
            <button @click="submitPos" class="btn btn-primary flex-1">
              保存
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
