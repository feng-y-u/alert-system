<template>
  <div class="layout">
    <!-- 左侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapse }">
      <div class="sidebar-header">
        <div class="logo">
          <div class="logo-icon">TF</div>
          <span v-if="!isCollapse" class="logo-text">校园监测平台</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          :class="['nav-item', { disabled: item.disabled }]"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span v-if="!isCollapse" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <!-- 顶部栏 -->
      <header class="top-bar">
        <div class="top-bar-left">
          <button class="toggle-btn" @click="toggleCollapse">
            <el-icon :size="20">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </button>
          <h1 class="page-title">{{ pageTitle }}</h1>
        </div>

        <div class="top-bar-right">
          <el-dropdown trigger="click" @command="handleCommand">
            <div class="user-menu">
              <div class="user-avatar">
                {{ username.charAt(0).toUpperCase() }}
              </div>
              <span class="user-name">{{ username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- 页面内容 -->
      <div class="page-content">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  Monitor,
  Document,
  WarningFilled,
  ArrowDown,
  Expand,
  Fold,
  SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapse = ref(false)
const toggleCollapse = () => (isCollapse.value = !isCollapse.value)

const username = computed(() => authStore.username || '用户')

const pageTitle = computed(() => {
  const titles = {
    '/': '仪表盘',
    '/login-logs': '登录日志',
    '/alerts': '告警列表',
  }
  return titles[route.path] || '仪表盘'
})

const menuItems = [
  { path: '/', label: '仪表盘', icon: Monitor, disabled: false },
  { path: '/login-logs', label: '登录日志', icon: Document, disabled: false },
  { path: '/alerts', label: '告警列表', icon: WarningFilled, disabled: false },
]

const handleCommand = (cmd) => {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--color-bg);
}

/* === 侧边栏 === */
.sidebar {
  width: 260px;
  background-color: var(--color-bg-elevated);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar.collapsed {
  width: 72px;
}

.sidebar-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  background: linear-gradient(135deg, #111827 0%, #374151 100%);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.logo-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
}

/* === 导航菜单 === */
.sidebar-nav {
  flex: 1;
  padding: 16px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 10px;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: all 0.2s ease;
  font-weight: 500;
}

.nav-item:hover:not(.disabled) {
  background-color: var(--color-border-light);
  color: var(--color-text-primary);
}

.nav-item.active,
.nav-item.router-link-exact-active {
  background-color: var(--color-border-light);
  color: var(--color-primary);
  font-weight: 600;
}

.nav-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.nav-label {
  font-size: 14px;
  white-space: nowrap;
}

/* === 主内容区 === */
.main-content {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  transition: margin-left 0.3s ease;
}

.sidebar.collapsed + .main-content {
  margin-left: 72px;
}

/* === 顶部栏 === */
.top-bar {
  height: 72px;
  background-color: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  position: sticky;
  top: 0;
  z-index: 50;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.toggle-btn {
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-border);
  border-radius: 10px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s ease;
}

.toggle-btn:hover {
  background-color: var(--color-border-light);
  color: var(--color-text-primary);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.top-bar-right {
  display: flex;
  align-items: center;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-menu:hover {
  background-color: var(--color-border-light);
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* === 页面内容 === */
.page-content {
  flex: 1;
  padding: 32px;
}
</style>