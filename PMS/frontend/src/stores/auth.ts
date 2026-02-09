/**
 * 认证状态存储
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

// 用户角色类型
export type UserRole = 'admin' | 'manager' | 'staff'

// 用户信息接口
export interface UserInfo {
  id: string
  username: string
  realName: string
  roles: UserRole[]  // 支持多角色
  departmentId?: string
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.roles?.includes('admin') ?? false)
  const isManager = computed(() => 
    user.value?.roles?.includes('manager') || user.value?.roles?.includes('admin') || false
  )

  // 登录
  async function login(username: string, password: string) {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)

    const response = await api.post('/api/auth/login', params)
    
    token.value = response.data.access_token
    
    // 处理 roles 数组
    let roles: UserRole[] = []
    if (response.data.roles) {
      roles = response.data.roles
    } else if (response.data.role) {
      // 兼容旧接口
      roles = [response.data.role]
    }
    
    user.value = {
      id: response.data.user_id,
      username: response.data.username,
      realName: response.data.real_name,
      roles: roles,
      departmentId: response.data.department_id
    }

    localStorage.setItem('token', token.value!)
  }

  // 登出
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  // 获取当前用户信息
  async function fetchCurrentUser() {
    if (!token.value) return

    try {
      const response = await api.get('/api/auth/me')
      
      // 处理 roles 数组
      let roles: UserRole[] = []
      if (response.data.roles) {
        roles = response.data.roles
      } else if (response.data.role) {
        roles = [response.data.role]
      }
      
      user.value = {
        id: response.data.id,
        username: response.data.username,
        realName: response.data.real_name,
        roles: roles,
        departmentId: response.data.department_id
      }
    } catch {
      logout()
    }
  }

  // 检查是否拥有指定角色
  function hasRole(role: UserRole): boolean {
    return user.value?.roles?.includes(role) ?? false
  }

  // 检查是否拥有任一指定角色
  function hasAnyRole(roles: UserRole[]): boolean {
    return roles.some(role => user.value?.roles?.includes(role))
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isManager,
    login,
    logout,
    fetchCurrentUser,
    hasRole,
    hasAnyRole
  }
})

