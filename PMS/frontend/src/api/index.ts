/**
 * Axios API 客户端配置
 */
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

// 创建 axios 实例
const api = axios.create({
  baseURL: '',
  timeout: 10000
})

// 请求拦截器 - 添加 Authorization 头
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 令牌过期，登出
      const authStore = useAuthStore()
      authStore.logout()
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
