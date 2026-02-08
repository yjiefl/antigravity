/**
 * Vue Router 路由配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue')
      },
      {
        path: 'tasks',
        name: 'TaskList',
        component: () => import('../views/TaskList.vue')
      },
      {
        path: 'tasks/new',
        name: 'TaskCreate',
        component: () => import('../views/TaskForm.vue')
      },
      {
        path: 'tasks/:id',
        name: 'TaskDetail',
        component: () => import('../views/TaskDetail.vue')
      },
      {
        path: 'kpi',
        name: 'KPI',
        component: () => import('../views/KPI.vue')
      },
      {
        path: 'appeals/review',
        name: 'AppealsReview',
        component: () => import('../views/AppealsReview.vue'),
        meta: { requiresAuth: true, roles: ['admin', 'manager'] }
      },
      {
        path: 'admin/org',
        name: 'OrgManager',
        component: () => import('../views/admin/OrgManager.vue'),
        meta: { requiresAuth: true, roles: ['admin'] } 
      },
      {
        path: 'help',
        name: 'Help',
        component: () => import('../views/Help.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
