<script setup lang="ts">
/**
 * 组织架构管理
 *
 * 展示公司-部门-岗位树形结构，支持完整增删改查
 */
import { ref, onMounted } from "vue";
import api from "../../api";
import { useAuthStore } from "../../stores/auth";
import OrgTreeItem from "../../components/OrgTreeItem.vue";

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
const errorMsg = ref("");

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

/**
 * 提取后端返回的错误信息
 */
function extractError(e: any): string {
  return e.response?.data?.detail || e.message || "操作失败";
}

// === 公司操作 ===
function openAddOrg() {
  isEdit.value = false;
  orgForm.value = { id: "", name: "", code: "" };
  errorMsg.value = "";
  showOrgModal.value = true;
}

function openEditOrg(org: any) {
  isEdit.value = true;
  orgForm.value = { id: org.id, name: org.name, code: org.code || "" };
  errorMsg.value = "";
  showOrgModal.value = true;
}

async function submitOrg() {
  errorMsg.value = "";
  try {
    if (isEdit.value) {
      await api.put(`/api/org/organizations/${orgForm.value.id}`, {
        name: orgForm.value.name,
        code: orgForm.value.code || null,
      });
    } else {
      await api.post("/api/org/organizations", {
        name: orgForm.value.name,
        code: orgForm.value.code || null,
      });
    }
    showOrgModal.value = false;
    await loadTree();
  } catch (e: any) {
    errorMsg.value = extractError(e);
  }
}

async function deleteOrg(id: string) {
  if (!confirm("确认删除该公司？如果有部门将无法删除。")) return;
  try {
    await api.delete(`/api/org/organizations/${id}`);
    await loadTree();
  } catch (e: any) {
    alert(extractError(e));
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
    parent_id: parent.type === "department" ? parent.id : "",
    organization_id: orgId,
  };
  errorMsg.value = "";
  showDeptModal.value = true;
}

function openEditDept(dept: any) {
  isEdit.value = true;
  currentNode.value = null;
  deptForm.value = {
    id: dept.id,
    name: dept.name,
    code: dept.code || "",
    parent_id: dept.parent_id || "",
    organization_id: dept.organization_id || "",
  };
  errorMsg.value = "";
  showDeptModal.value = true;
}

async function submitDept() {
  errorMsg.value = "";
  try {
    if (isEdit.value) {
      await api.put(`/api/org/departments/${deptForm.value.id}`, {
        name: deptForm.value.name,
        code: deptForm.value.code || null,
      });
    } else {
      const payload: any = {
        name: deptForm.value.name,
        code: deptForm.value.code || null,
        organization_id: deptForm.value.organization_id,
      };
      // 只有在部门下新增子部门时才传 parent_id
      if (deptForm.value.parent_id) {
        payload.parent_id = deptForm.value.parent_id;
      }
      await api.post("/api/org/departments", payload);
    }
    showDeptModal.value = false;
    await loadTree();
  } catch (e: any) {
    errorMsg.value = extractError(e);
  }
}

async function deleteDept(id: string) {
  if (!confirm("确认删除该部门？如果有子部门、岗位或人员将无法删除。")) return;
  try {
    await api.delete(`/api/org/departments/${id}`);
    await loadTree();
  } catch (e: any) {
    alert(extractError(e));
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
  errorMsg.value = "";
  showPosModal.value = true;
}

function openEditPos(pos: any) {
  isEdit.value = true;
  currentNode.value = null;
  posForm.value = {
    id: pos.id,
    name: pos.name,
    code: pos.code || "",
    department_id: pos.department_id || "",
    can_assign_task: pos.can_assign || false,
    can_transfer_task: pos.can_transfer || false,
  };
  errorMsg.value = "";
  showPosModal.value = true;
}

async function submitPos() {
  errorMsg.value = "";
  try {
    if (isEdit.value) {
      await api.put(`/api/org/positions/${posForm.value.id}`, {
        name: posForm.value.name,
        code: posForm.value.code || null,
        can_assign_task: posForm.value.can_assign_task,
        can_transfer_task: posForm.value.can_transfer_task,
      });
    } else {
      await api.post("/api/org/positions", {
        name: posForm.value.name,
        code: posForm.value.code || null,
        department_id: posForm.value.department_id,
        can_assign_task: posForm.value.can_assign_task,
        can_transfer_task: posForm.value.can_transfer_task,
      });
    }
    showPosModal.value = false;
    await loadTree();
  } catch (e: any) {
    errorMsg.value = extractError(e);
  }
}

async function deletePos(id: string) {
  if (!confirm("确认删除该岗位？如果有用户关联将无法删除。")) return;
  try {
    await api.delete(`/api/org/positions/${id}`);
    await loadTree();
  } catch (e: any) {
    alert(extractError(e));
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
      <div class="p-6">
        <OrgTreeItem
          v-for="org in treeData"
          :key="org.id"
          :node="org"
          :depth="0"
          :expanded-keys="expandedKeys"
          @toggle-expand="toggleExpand"
          @add-dept="openAddDept"
          @add-pos="openAddPos"
          @edit-dept="openEditDept"
          @delete-dept="deleteDept"
          @edit-pos="openEditPos"
          @delete-pos="deletePos"
          @edit-org="openEditOrg"
          @delete-org="deleteOrg"
        />
        <div
          v-if="treeData.length === 0"
          class="text-center py-8 text-slate-400"
        >
          暂无组织架构数据，请先新增公司
        </div>
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
          <div
            v-if="errorMsg"
            class="text-sm text-red-500 bg-red-50 p-2 rounded"
          >
            {{ errorMsg }}
          </div>
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
          <div v-if="currentNode && !isEdit" class="text-sm text-slate-500">
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
          <div
            v-if="errorMsg"
            class="text-sm text-red-500 bg-red-50 p-2 rounded"
          >
            {{ errorMsg }}
          </div>
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
        <h3 class="font-bold mb-4">{{ isEdit ? "编辑" : "新增" }}岗位</h3>
        <div class="space-y-4">
          <div v-if="currentNode && !isEdit" class="text-sm text-slate-500">
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
          <div class="flex items-center gap-2">
            <input
              type="checkbox"
              v-model="posForm.can_transfer_task"
              id="can_transfer"
            />
            <label for="can_transfer" class="text-sm">允许转办任务</label>
          </div>
          <div
            v-if="errorMsg"
            class="text-sm text-red-500 bg-red-50 p-2 rounded"
          >
            {{ errorMsg }}
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
