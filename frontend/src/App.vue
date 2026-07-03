<template>
  <router-view />
</template>

<script setup>
</script>

<style>
/* === 设计 Token 覆盖 Element Plus 默认主题 === */
:root {
  --el-color-primary: #2563eb;
  --el-color-primary-light-3: #3b82f6;
  --el-color-primary-light-5: #60a5fa;
  --el-color-primary-light-7: #93c5fd;
  --el-color-primary-light-8: #bfdbfe;
  --el-color-primary-light-9: #dbeafe;
  --el-color-primary-dark-2: #1d4ed8;
  --el-color-success: #10b981;
  --el-color-warning: #f59e0b;
  --el-color-danger: #ef4444;
  --el-color-info: #6b7280;
  --el-bg-color: #f8f9fa;
  --el-bg-color-overlay: #ffffff;
  --el-border-color: #e5e7eb;
  --el-border-color-light: #d1d5db;
  --el-border-color-lighter: #e5e7eb;
  --el-border-color-extra-light: #f3f4f6;
  --el-text-color-primary: #111827;
  --el-text-color-regular: #374151;
  --el-text-color-secondary: #6b7280;
  --el-text-color-placeholder: #9ca3af;
  --el-font-size-base: 14px;
  --el-font-size-small: 13px;
  --el-font-size-extra-small: 12px;
  --el-font-size-medium: 14px;
  --el-font-size-large: 16px;
  --el-font-weight-primary: 400;
  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
  --el-border-radius-round: 20px;
  --el-border-radius-circle: 999px;
}

/* === 全局重置 & 字体 === */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Inter', 'Noto Sans SC', -apple-system, 'Helvetica Neue',
    'PingFang SC', 'Microsoft YaHei', sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: #111827;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* === 按钮统一样式覆盖 === */
.el-button {
  font-weight: 400 !important;
  font-size: 14px !important;
  --el-button-font-weight: 400;
  border-radius: 8px !important;
  height: 36px;
}

.el-button--primary {
  --el-button-bg-color: #2563eb;
  --el-button-hover-bg-color: #3b82f6;
  --el-button-active-bg-color: #1d4ed8;
}

/* === 卡片统一样式 === */
.el-card {
  border: 1px solid #e5e7eb !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  background: #ffffff;
}

.el-card.is-hover-shadow:hover {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
}

/* === 输入框统一样式 === */
.el-input__wrapper,
.el-input__inner {
  border-radius: 8px !important;
}

.el-input__wrapper {
  box-shadow: 0 0 0 1px #d1d5db inset !important;
}

.el-input__wrapper.is-focus {
  box-shadow: 0 0 0 1px #2563eb inset !important;
}

/* === 表格统一样式 === */
.el-table {
  --el-table-border-color: transparent;
  --el-table-header-bg-color: transparent;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #f3f4f6;
}

.el-table th.el-table__cell {
  font-weight: 500;
  font-size: 13px;
  color: #6b7280;
  border-bottom: 1px solid #e5e7eb;
}

.el-table td.el-table__cell {
  border-bottom: 1px solid #f3f4f6;
  padding: 12px;
}
</style>
