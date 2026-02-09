<script setup lang="ts">
/**
 * 用户管理页面
 */
import { ref, onMounted, reactive } from "vue";
import api from "../../api";

const users = ref<any[]>([]);
const loading = ref(false);
const keyword = ref("");
const showCreateModal = ref(false);
const showEditModal = ref(false);
const showResetPwdModal = ref(false);

const userForm = reactive({
  id: "",
  username: "",
  real_name: "",
  password: "", // Only for create
  roles: [] as string[],
  department_id: "",
  position_id: "",
  is_active: true,
});

const resetPwdForm = reactive({
  id: "",
  username: "",
  new_password: "",
});

const departments = ref<any[]>([]);
const positions = ref<any[]>([]);

// 加载用户列表
async function fetchUsers() {
  loading.value = true;
  try {
    const params: any = { limit: 100 };
    if (keyword.value) {
      params.keyword = keyword.value;
    }
    const res = await api.get("/api/users/manage", { params });
    users.value = res.data;
  } catch (e) {
    console.error("加载用户失败", e);
  } finally {
    loading.value = false;
  }
}

// 加载部门和岗位
async function fetchOrganization() {
  try {
    const res = await api.get("/api/org/organizations");
    const org = res.data[0]; // 假设只有一个公司
    if (org) {
      departments.value = org.departments;
      // 扁平化岗位列表
      positions.value = org.departments.flatMap((d: any) => d.positions);
    }
  } catch (e) {
    console.error("加载组织架构失败", e);
  }
}

function openCreateModal() {
  Object.assign(userForm, {
    id: "",
    username: "",
    real_name: "",
    password: "",
    roles: ["staff"],
    department_id: "",
    position_id: "",
    is_active: true,
  });
  showCreateModal.value = true;
}

function openEditModal(user: any) {
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    real_name: user.real_name,
    password: "", 
    roles: user.roles || ["staff"],
    department_id: user.department_id || "",
    position_id: user.position_id || "",
    is_active: user.is_active,
  });
  showEditModal.value = true;
}

function openResetPwdModal(user: any) {
  resetPwdForm.id = user.id;
  resetPwdForm.username = user.username;
  resetPwdForm.new_password = "";
  showResetPwdModal.value = true;
}

async function createUser() {
  if (!userForm.username || !userForm.real_name || !userForm.password) {
    alert("请填写必填项");
    return;
  }
  try {
    const { id, ...payload } = userForm as any;
    // 如果是空字符串，转换为 null，否则后端 UUID 验证会失败
    if (!payload.department_id) payload.department_id = null;
    if (!payload.position_id) payload.position_id = null;

    await api.post("/api/users", payload);
    showCreateModal.value = false;
    fetchUsers();
  } catch (e: any) {
    console.error("创建失败", e);
    const detail = e.response?.data?.detail;
    let msg = "";
    if (Array.isArray(detail)) {
      msg = detail.map((d: any) => `${d.loc.join(".")}: ${d.msg}`).join("\n");
    } else {
      msg = detail || e.message;
    }
    alert("创建失败:\n" + msg);
  }
}

async function updateUser() {
  try {
    const { id, password, ...data } = userForm;
    const payload: any = { ...data };
    if (!payload.department_id) payload.department_id = null;
    if (!payload.position_id) payload.position_id = null;

    await api.put(`/api/users/${id}`, payload);
    showEditModal.value = false;
    fetchUsers();
  } catch (e: any) {
    console.error("更新失败", e);
    const detail = e.response?.data?.detail;
    let msg = "";
    if (Array.isArray(detail)) {
      msg = detail.map((d: any) => `${d.loc.join(".")}: ${d.msg}`).join("\n");
    } else {
      msg = detail || e.message;
    }
    alert("更新失败:\n" + msg);
  }
}

async function toggleStatus(user: any) {
  if (!confirm(`确认${user.is_active ? "禁用" : "启用"}该用户？`)) return;
  try {
    await api.patch(`/api/users/${user.id}/status`, null, {
      params: { active: !user.is_active },
    });
    fetchUsers();
  } catch (e: any) {
    alert("操作失败: " + (e.response?.data?.detail || e.message));
  }
}

async function resetPassword() {
  if (!resetPwdForm.new_password || resetPwdForm.new_password.length < 6) {
    alert("密码长度至少6位");
    return;
  }
  try {
    await api.post(`/api/users/${resetPwdForm.id}/reset-password`, {
      new_password: resetPwdForm.new_password,
    });
    alert("密码重置成功");
    showResetPwdModal.value = false;
  } catch (e: any) {
    alert("重置失败: " + (e.response?.data?.detail || e.message));
  }
}

onMounted(() => {
  fetchUsers();
  fetchOrganization();
});
</script>

<template>
  <div class="space-y-6">
    <div class="flex justify-between items-center">
      <h1 class="text-2xl font-bold text-slate-800">👥 用户管理</h1>
      <button @click="openCreateModal" class="btn btn-primary">
        + 新增用户
      </button>
    </div>

    <!-- 搜索栏 -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-100 flex gap-4">
      <div class="flex-1 relative">
        <input
          v-model="keyword"
          @keyup.enter="fetchUsers"
          type="text"
          placeholder="搜索用户名或姓名..."
          class="w-full pl-10 pr-4 py-2 border rounded-lg outline-none focus:ring-2 focus:ring-indigo-100"
        />
        <span class="absolute left-3 top-2.5 text-slate-400">🔍</span>
      </div>
      <button @click="fetchUsers" class="btn btn-secondary">查询</button>
    </div>

    <!-- 用户列表 -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
      <table class="w-full">
        <thead class="bg-slate-50 border-b border-slate-100">
          <tr>
            <th class="px-6 py-4 text-left text-sm font-bold text-slate-600">用户</th>
            <th class="px-6 py-4 text-left text-sm font-bold text-slate-600">部门/岗位</th>
            <th class="px-6 py-4 text-left text-sm font-bold text-slate-600">角色</th>
            <th class="px-6 py-4 text-left text-sm font-bold text-slate-600">状态</th>
            <th class="px-6 py-4 text-right text-sm font-bold text-slate-600">操作</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading">
            <td colspan="5" class="p-8 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="users.length === 0">
            <td colspan="5" class="p-8 text-center text-slate-400">暂无数据</td>
          </tr>
          <tr v-for="user in users" :key="user.id" class="hover:bg-slate-50 transition-colors">
            <td class="px-6 py-4">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold">
                  {{ user.real_name.charAt(0) }}
                </div>
                <div>
                  <div class="font-bold text-slate-800">{{ user.real_name }}</div>
                  <div class="text-xs text-slate-500">@{{ user.username }}</div>
                </div>
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-slate-600">
               <!-- 简单的显示，实际应该根据id查找部门名称，或者后端直接返回名称 -->
               <!-- 这里假设后端UserResponse还没带名称，暂时留空或仅显示ID，
                    后续优化可以在UserResponse增加department_name字段 -->
                <span v-if="user.department_id">已分配部门</span>
                <span v-else class="text-slate-400">-</span>
            </td>
            <td class="px-6 py-4">
              <div class="flex gap-1 flex-wrap">
                <span v-for="role in user.roles" :key="role" 
                  class="px-2 py-0.5 rounded text-xs font-bold uppercase"
                  :class="{
                    'bg-purple-100 text-purple-700': role === 'admin',
                    'bg-blue-100 text-blue-700': role === 'manager',
                    'bg-slate-100 text-slate-600': role === 'staff'
                  }"
                >
                  {{ role }}
                </span>
              </div>
            </td>
            <td class="px-6 py-4">
              <span v-if="user.is_active" class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-bold">启用</span>
              <span v-else class="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-bold">禁用</span>
            </td>
            <td class="px-6 py-4 text-right space-x-2">
              <button @click="openEditModal(user)" class="text-indigo-600 hover:text-indigo-800 text-sm font-bold">编辑</button>
              <button @click="openResetPwdModal(user)" class="text-orange-600 hover:text-orange-800 text-sm font-bold">重置密码</button>
              <button 
                @click="toggleStatus(user)" 
                class="text-sm font-bold"
                :class="user.is_active ? 'text-red-600 hover:text-red-800' : 'text-green-600 hover:text-green-800'"
              >
                {{ user.is_active ? '禁用' : '启用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 创建/编辑模态框 -->
    <div v-if="showCreateModal || showEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div class="bg-white rounded-xl w-full max-w-lg p-6 animate-fade-in-up">
        <h3 class="text-xl font-bold mb-4">{{ showCreateModal ? '新增用户' : '编辑用户' }}</h3>
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-bold text-slate-700 mb-1">用户名 *</label>
              <input v-model="userForm.username" type="text" class="w-full px-3 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-100 transition-shadow" :disabled="showEditModal">
            </div>
            <div>
              <label class="block text-sm font-bold text-slate-700 mb-1">真实姓名 *</label>
              <input v-model="userForm.real_name" type="text" class="w-full px-3 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-100 transition-shadow">
            </div>
          </div>
          
          <div v-if="showCreateModal">
            <label class="block text-sm font-bold text-slate-700 mb-1">初始密码 *</label>
            <input v-model="userForm.password" type="password" class="w-full px-3 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-100 transition-shadow">
          </div>



          <div>
             <label class="block text-sm font-bold text-slate-700 mb-1">角色</label>
             <div class="flex gap-4">
               <label class="flex items-center gap-2">
                 <input type="checkbox" v-model="userForm.roles" value="admin"> 管理员
               </label>
               <label class="flex items-center gap-2">
                 <input type="checkbox" v-model="userForm.roles" value="manager"> 主管
               </label>
               <label class="flex items-center gap-2">
                 <input type="checkbox" v-model="userForm.roles" value="staff"> 员工
               </label>
             </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-bold text-slate-700 mb-1">部门</label>
              <select v-model="userForm.department_id" class="w-full px-3 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-100 transition-shadow">
                <option value="">未分配</option>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-bold text-slate-700 mb-1">岗位</label>
              <select v-model="userForm.position_id" class="w-full px-3 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-100 transition-shadow">
                <option value="">未分配</option>
                <option v-for="p in positions" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
          </div>

          <div class="flex gap-3 pt-4">
            <button @click="showCreateModal = false; showEditModal = false" class="btn btn-secondary flex-1">取消</button>
            <button @click="showCreateModal ? createUser() : updateUser()" class="btn btn-primary flex-1">保存</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 重置密码模态框 -->
    <div v-if="showResetPwdModal" class="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
        <div class="bg-white rounded-xl w-full max-w-sm p-6 animate-fade-in-up">
            <h3 class="text-xl font-bold mb-4">重置密码</h3>
            <p class="text-sm text-slate-500 mb-4">正在重置用户 <b>{{ resetPwdForm.username }}</b> 的密码</p>
            <div class="mb-4">
                <label class="block text-sm font-bold text-slate-700 mb-1">新密码 *</label>
                <input v-model="resetPwdForm.new_password" type="text" class="w-full px-3 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-100 transition-shadow" placeholder="至少6位">
            </div>
            <div class="flex gap-3">
                <button @click="showResetPwdModal = false" class="btn btn-secondary flex-1">取消</button>
                <button @click="resetPassword" class="btn btn-primary flex-1">确认重置</button>
            </div>
        </div>
    </div>

  </div>
</template>
