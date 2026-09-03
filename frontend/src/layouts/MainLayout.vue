<template>
  <div class="layout" :class="{ 'layout--collapsed': isCollapse }">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar__brand">
        <div class="brand">
          <span class="brand__mark">
            <el-icon :size="17"><Lock /></el-icon>
          </span>
          <Transition name="fade">
            <span v-if="!isCollapse" class="brand__text">
              <span class="brand__name">校园监测平台</span>
              <span class="brand__sub">安全审计与日志分析</span>
            </span>
          </Transition>
        </div>
      </div>

      <nav class="sidebar__nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :title="isCollapse ? item.label : ''"
        >
          <el-icon :size="19"><component :is="item.icon" /></el-icon>
          <span v-if="!isCollapse" class="nav-item__label">{{ item.label }}</span>
          <span
            v-if="item.badge && unreadCount > 0"
            class="nav-item__badge num"
            :class="isCollapse ? 'nav-item__badge--dot' : 'nav-item__badge--danger'"
          >
            {{ isCollapse ? '' : unreadCount }}
          </span>
        </router-link>
      </nav>

      <div class="sidebar__footer">
        <button class="collapse-btn" @click="isCollapse = !isCollapse">
          <el-icon :size="18">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <span v-if="!isCollapse" class="collapse-btn__text">收起侧边栏</span>
        </button>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="main">
      <header class="topbar">
        <div class="topbar__left">
          <button class="icon-btn topbar__toggle" @click="isCollapse = !isCollapse">
            <el-icon :size="18">
              <Fold v-if="!isCollapse" />
              <Expand v-else />
            </el-icon>
          </button>
          <div class="topbar__titles">
            <h1 class="topbar__title">{{ pageTitle }}</h1>
            <p class="topbar__desc">{{ pageDescription }}</p>
          </div>
        </div>

        <div class="topbar__right">
          <!-- SSE 连接状态：实时告警链路是否通，一眼可见 -->
          <el-tooltip
            :content="isConnected ? '实时告警推送已连接' : '实时告警推送未连接'"
            placement="bottom"
          >
            <span class="conn" :class="{ 'conn--on': isConnected }">
              <span class="conn__dot" />
              <span class="conn__text">{{ isConnected ? '实时' : '离线' }}</span>
            </span>
          </el-tooltip>

          <el-dropdown trigger="click" @command="handleCommand">
            <button class="user-menu">
              <span class="user-menu__avatar">{{ initial }}</span>
              <span class="user-menu__name">{{ username }}</span>
              <el-icon :size="14"><ArrowDown /></el-icon>
            </button>
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

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useNotificationStore } from '../stores/notification'
import {
  ArrowDown,
  DataLine,
  Document,
  Expand,
  Fold,
  Lock,
  Setting,
  SwitchButton,
  WarningFilled,
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const isCollapse = ref(false)

const navItems = [
  { path: '/', label: '仪表盘', icon: DataLine, badge: false },
  { path: '/login-logs', label: '登录日志', icon: Document, badge: false },
  { path: '/alerts', label: '告警列表', icon: WarningFilled, badge: true },
  { path: '/settings', label: '系统设置', icon: Setting, badge: false },
]

const PAGE_META = {
  '/': { title: '仪表盘', desc: '校园登录行为与异常告警总览' },
  '/login-logs': { title: '登录日志', desc: '查询与审计校园系统的登录记录' },
  '/alerts': { title: '告警列表', desc: '处理检测出的异常登录告警' },
  '/settings': { title: '系统设置', desc: '查看与验证平台运行配置' },
}

const username = computed(() => authStore.username || '用户')
const initial = computed(() => username.value.charAt(0).toUpperCase())
const unreadCount = computed(() => notificationStore.unreadCount)
const isConnected = computed(() => notificationStore.isConnected)

const pageTitle = computed(() => PAGE_META[route.path]?.title ?? '仪表盘')
const pageDescription = computed(() => PAGE_META[route.path]?.desc ?? '')

function handleCommand(cmd) {
  if (cmd === 'logout') {
    authStore.logout()
    router.push('/login')
  }
}

onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) notificationStore.connect(token)
})

onUnmounted(() => {
  notificationStore.disconnect()
})
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-app);
}

/* ============ 侧边栏（浅色） ============ */
.sidebar {
  position: fixed;
  inset: 0 auto 0 0;
  width: var(--nav-w);
  background: var(--nav-bg);
  border-right: 1px solid var(--nav-border);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: width var(--dur) var(--ease);
}

.layout--collapsed .sidebar {
  width: var(--nav-w-collapsed);
}

.sidebar__brand {
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  padding: 0 18px;
  border-bottom: 1px solid var(--nav-border);
  flex-shrink: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  overflow: hidden;
}

.brand__mark {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
}

.brand__text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.brand__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--nav-text-strong);
  white-space: nowrap;
}

.brand__sub {
  font-size: 11px;
  color: var(--text-faint);
  white-space: nowrap;
}

.sidebar__nav {
  flex: 1;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--r-sm);
  color: var(--nav-text);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}

.layout--collapsed .nav-item {
  justify-content: center;
  padding: 10px 0;
}

.nav-item:hover {
  background: var(--nav-bg-soft);
  color: var(--nav-text-strong);
}

/* 激活态：浅蓝药丸 + 左侧色条 */
.nav-item.router-link-exact-active {
  background: var(--brand-50);
  color: var(--brand-600);
  font-weight: 600;
}

.nav-item.router-link-exact-active::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 20%;
  bottom: 20%;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--brand-600);
}

.layout--collapsed .nav-item.router-link-exact-active::before {
  left: -12px;
}

.nav-item__label {
  flex: 1;
  min-width: 0;
}

.nav-item__badge {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: var(--r-full);
  background: var(--bg-hover);
  color: var(--text-muted);
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 未读告警用红色徽标 */
.nav-item__badge--danger {
  background: var(--danger);
  color: #fff;
}

/* 折叠态退化成一个小红点 */
.nav-item__badge--dot {
  position: absolute;
  top: 8px;
  right: 12px;
  min-width: 0;
  width: 8px;
  height: 8px;
  padding: 0;
  border-radius: 50%;
  background: var(--danger);
  box-shadow: 0 0 0 2px var(--nav-bg);
}

.sidebar__footer {
  padding: 12px;
  border-top: 1px solid var(--nav-border);
  flex-shrink: 0;
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 9px 12px;
  border-radius: var(--r-sm);
  color: var(--nav-text);
  font-size: 13px;
  transition: background var(--dur) var(--ease), color var(--dur) var(--ease);
}

.layout--collapsed .collapse-btn {
  justify-content: center;
  padding: 9px 0;
}

.collapse-btn:hover {
  background: var(--nav-bg-soft);
  color: var(--nav-text-strong);
}

/* ============ 主区域 ============ */
.main {
  flex: 1;
  min-width: 0;
  margin-left: var(--nav-w);
  display: flex;
  flex-direction: column;
  transition: margin-left var(--dur) var(--ease);
}

.layout--collapsed .main {
  margin-left: var(--nav-w-collapsed);
}

.topbar {
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 0 28px;
  background: rgba(255, 255, 255, 0.86);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--nav-border);
  position: sticky;
  top: 0;
  z-index: 50;
}

.topbar__left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.topbar__toggle {
  display: none;
}

.icon-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border);
  border-radius: var(--r-sm);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--dur) var(--ease);
}

.icon-btn:hover {
  background: var(--bg-hover);
  color: var(--text-strong);
}

.topbar__titles {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar__title {
  font-size: 17px;
  font-weight: 600;
  color: var(--text-strong);
  line-height: 1.3;
}

.topbar__desc {
  font-size: 12px;
  color: var(--text-faint);
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.topbar__right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

/* 实时连接指示 */
.conn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 11px;
  border-radius: var(--r-full);
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
}

.conn__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-faint);
}

.conn--on {
  background: var(--success-soft);
  border-color: transparent;
  color: var(--success-ink);
}

.conn--on .conn__dot {
  background: var(--success);
  animation: pulse 2s var(--ease) infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 5px 10px 5px 5px;
  border-radius: var(--r-full);
  color: var(--text-body);
  transition: background var(--dur) var(--ease);
}

.user-menu:hover {
  background: var(--bg-hover);
}

.user-menu__avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--brand-500), var(--brand-700));
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-menu__name {
  font-size: 14px;
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content {
  flex: 1;
  padding: 24px 28px 32px;
  min-width: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s var(--ease);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 1100px) {
  .topbar__toggle {
    display: flex;
  }
}

@media (max-width: 768px) {
  .topbar {
    padding: 0 16px;
  }

  .topbar__desc,
  .conn__text,
  .user-menu__name {
    display: none;
  }

  .content {
    padding: 16px;
  }
}
</style>
