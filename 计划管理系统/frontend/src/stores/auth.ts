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
  role: UserRole
}

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<UserInfo | null>(null)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isManager = computed(() => user.value?.role === 'manager' || user.value?.role === 'admin')

  // 登录
  async function login(username: string, password: string) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/api/auth/login', formData)
    
    token.value = response.data.access_token
    user.value = {
      id: response.data.user_id,
      username: response.data.username,
      realName: response.data.real_name,
      role: response.data.role
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
      user.value = {
        id: response.data.id,
        username: response.data.username,
        realName: response.data.real_name,
        role: response.data.role
      }
    } catch {
      logout()
    }
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    isManager,
    login,
    logout,
    fetchCurrentUser
  }
})
