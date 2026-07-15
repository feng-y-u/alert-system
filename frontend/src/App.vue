<template>
  <OfflineBanner
    :isOnline="isOnline"
    :wasOffline="wasOffline"
    @reconnected="onReconnected"
  />
  <router-view />
</template>

<script setup>
import { useOnline } from './composables/useOnline'
import { useNotificationStore } from './stores/notification'
import OfflineBanner from './components/common/OfflineBanner.vue'

const { isOnline, wasOffline, resetOfflineFlag } = useOnline()
const notificationStore = useNotificationStore()

function onReconnected() {
  resetOfflineFlag()
  const token = localStorage.getItem('token')
  if (token) {
    notificationStore.fetchLatestAlertsOnReconnect(token)
  }
}
</script>

<style>
/* === 设计 Token - 参考 Trueform CRM 风格 === */
:root {
  /* 主色调 - 深灰黑 */
  --color-primary: #111827;
  --color-primary-light: #374151;
  --color-primary-lighter: #6b7280;

  /* 背景色 */
  --color-bg: #f9fafb;
  --color-bg-elevated: #ffffff;
  --color-bg-sidebar: #ffffff;

  /* 文字颜色 */
  --color-text-primary: #111827;
  --color-text-secondary: #6b7280;
  --color-text-tertiary: #9ca3af;
  --color-text-inverse: #ffffff;

  /* 边框与分割 */
  --color-border: #e5e7eb;
  --color-border-light: #f3f4f6;

  /* 状态色 */
  --color-success: #10b981;
  --color-success-light: #d1fae5;
  --color-warning: #f59e0b;
  --color-warning-light: #fef3c7;
  --color-danger: #ef4444;
  --color-danger-light: #fee2e2;
  --color-info: #3b82f6;

  /* Element Plus 覆盖 */
  --el-color-primary: #111827;
  --el-color-primary-light-3: #374151;
  --el-color-primary-light-5: #6b7280;
  --el-color-success: #10b981;
  --el-color-warning: #f59e0b;
  --el-color-danger: #ef4444;
  --el-color-info: #6b7280;
  --el-bg-color: #f9fafb;
  --el-bg-color-overlay: #ffffff;
  --el-border-color: #e5e7eb;
  --el-border-color-light: #f3f4f6;
  --el-text-color-primary: #111827;
  --el-text-color-regular: #374151;
  --el-text-color-secondary: #6b7280;
  --el-border-radius-base: 12px;
  --el-border-radius-small: 8px;
}

/* === 全局重置 === */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 14px;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
    'Helvetica Neue', Arial, sans-serif;
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-text-primary);
  background-color: var(--color-bg);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* === 字体层级 === */
.text-display {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  color: var(--color-text-primary);
}

.text-heading {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
  color: var(--color-text-primary);
}

.text-title {
  font-size: 18px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--color-text-primary);
}

.text-subtitle {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.5;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.text-body {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-text-primary);
}

.text-caption {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--color-text-tertiary);
}

/* === 按钮样式 === */
.el-button {
  font-weight: 500 !important;
  border-radius: 8px !important;
  height: 40px;
  padding: 0 20px !important;
  transition: all 0.2s ease !important;
}

.el-button--primary {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

.el-button--primary:hover {
  background-color: var(--color-primary-light) !important;
  border-color: var(--color-primary-light) !important;
}

/* === 卡片样式 === */
.el-card {
  border: none !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03) !important;
  background: var(--color-bg-elevated) !important;
}

.el-card__header {
  border-bottom: 1px solid var(--color-border) !important;
  padding: 20px 24px !important;
}

.el-card__body {
  padding: 24px !important;
}

/* === 输入框样式 === */
.el-input__wrapper {
  border-radius: 8px !important;
  box-shadow: 0 0 0 1px var(--color-border) inset !important;
  padding: 0 12px !important;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 2px var(--color-primary) inset !important;
}

.el-input__inner {
  height: 40px !important;
}

/* === 菜单样式 === */
.el-menu {
  border-right: none !important;
}

.el-menu-item {
  height: 44px !important;
  line-height: 44px !important;
  margin: 4px 12px !important;
  border-radius: 8px !important;
  font-weight: 500;
  color: var(--color-text-secondary) !important;
}

.el-menu-item.is-active {
  background-color: var(--color-border-light) !important;
  color: var(--color-primary) !important;
  font-weight: 600;
}

.el-menu-item:hover {
  background-color: var(--color-border-light) !important;
}

/* === 表格样式 === */
.el-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: var(--color-bg);
  --el-table-tr-bg-color: var(--color-bg-elevated);
}

.el-table th.el-table__cell {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: var(--color-bg) !important;
  border-bottom: 1px solid var(--color-border) !important;
  padding: 16px !important;
}

.el-table td.el-table__cell {
  border-bottom: 1px solid var(--color-border-light) !important;
  padding: 16px !important;
}

/* === 标签样式 === */
.el-tag {
  border-radius: 20px !important;
  font-weight: 500;
  padding: 4px 12px !important;
  height: auto !important;
}

/* === 下拉菜单 === */
.el-dropdown-menu {
  border-radius: 12px !important;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
  padding: 8px !important;
}

.el-dropdown-menu__item {
  border-radius: 8px !important;
  padding: 10px 16px !important;
}
</style>