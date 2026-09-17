import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    meta: { requiresAuth: false },
    component: () => import('../views/Login.vue'),
  },
  {
    path: '/change-password',
    name: 'ChangePassword',
    meta: { requiresAuth: true },
    component: () => import('../views/ChangePassword.vue'),
  },
  {
    path: '/',
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '/login-logs',
        name: 'LoginLogs',
        component: () => import('../views/LoginLogs.vue'),
      },
      {
        path: '/alerts',
        name: 'Alerts',
        component: () => import('../views/Alerts.vue'),
      },
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('../views/Settings.vue'),
      },
    ],
  },
  {
    // 兜底：未知路径回首页，避免渲染空白页
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const mustChange = localStorage.getItem('mustChangePassword') === '1'

  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.path === '/login' && token && !mustChange) {
    next('/')
  } else if (token && mustChange && to.path !== '/change-password') {
    // 初始口令未修改：强制先去改密（后端也会对它返回 403）
    next('/change-password')
  } else if (to.path === '/change-password' && !mustChange) {
    next('/')
  } else {
    next()
  }
})

export default router
