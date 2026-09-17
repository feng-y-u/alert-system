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
/* ============================================================
   设计 Token（2026-09 重写版）
   方向：全浅色界面，白色侧边栏，蓝系主色，
        无描边软阴影卡片，大圆角，信息密度克制
   ============================================================ */
:root {
  /* 品牌色（蓝） */
  --brand-50: #eff6ff;
  --brand-100: #dbeafe;
  --brand-200: #bfdbfe;
  --brand-300: #93c5fd;
  --brand-400: #60a5fa;
  --brand-500: #3b82f6;
  --brand-600: #2563eb;
  --brand-700: #1d4ed8;
  --brand-800: #1e40af;

  /* 侧边栏（浅色） */
  --nav-bg: #ffffff;
  --nav-bg-soft: #f3f6fb;
  --nav-border: #edf0f5;
  --nav-text: #64748b;
  --nav-text-strong: #0f172a;

  /* 背景层次 */
  --bg-app: #f3f5f9;
  --bg-surface: #ffffff;
  --bg-subtle: #f7f9fc;
  --bg-hover: #eef2f7;

  /* 文字层次 */
  --text-strong: #0f172a;
  --text-body: #334155;
  --text-muted: #64748b;
  --text-faint: #94a3b8;
  --text-inverse: #ffffff;

  /* 边框 */
  --border: #e6eaf1;
  --border-soft: #eff2f7;

  /* 状态色 */
  --success: #10b981;
  --success-soft: #d9f5ea;
  --success-ink: #047857;
  --warning: #f59e0b;
  --warning-soft: #fdf0d3;
  --warning-ink: #b45309;
  --danger: #ef4444;
  --danger-soft: #fde4e4;
  --danger-ink: #b91c1c;
  --info: #0ea5e9;
  --info-soft: #e0f2fe;
  --info-ink: #0369a1;

  /* 阴影（偏蓝的软阴影） */
  --shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.04);
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.03), 0 4px 14px rgba(15, 23, 42, 0.05);
  --shadow-md: 0 8px 28px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 18px 44px rgba(15, 23, 42, 0.12);

  /* 圆角 */
  --r-sm: 10px;
  --r-md: 14px;
  --r-lg: 18px;
  --r-xl: 24px;
  --r-full: 999px;

  /* 布局尺寸 */
  --nav-w: 248px;
  --nav-w-collapsed: 76px;
  --topbar-h: 66px;

  /* 动效：三个层级 + 三条曲线，避免所有交互共用同一套时长
     （数值与 utils/motion.js 的 DURATION / EASING 同源，改节奏时两边一起改） */
  --motion-fast: 140ms; /* 微交互：hover / 焦点 / 按下 */
  --motion-base: 220ms; /* 状态切换：展开 / Tab / 筛选 */
  --motion-slow: 380ms; /* 内容与图层入场 */
  --ease-standard: cubic-bezier(0.2, 0, 0.2, 1);
  --ease-enter: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-move: cubic-bezier(0.4, 0, 0.2, 1);

  /* 兼容仍在引用旧变量的页面（MainLayout / Login 等） */
  --dur: var(--motion-base);
  --ease: var(--ease-standard);

  /* ============================================================
     Element Plus 变量覆盖（组件内部沿用同一套视觉语言）
     ============================================================ */
  --el-color-primary: #2563eb;
  --el-color-primary-light-3: #3b82f6;
  --el-color-primary-light-5: #60a5fa;
  --el-color-primary-light-7: #93c5fd;
  --el-color-primary-light-8: #bfdbfe;
  --el-color-primary-light-9: #eff6ff;
  --el-color-primary-dark-2: #1d4ed8;
  --el-color-success: #10b981;
  --el-color-warning: #f59e0b;
  --el-color-danger: #ef4444;
  --el-color-error: #ef4444;
  --el-color-info: #64748b;

  --el-bg-color: #ffffff;
  --el-bg-color-page: #f3f5f9;
  --el-bg-color-overlay: #ffffff;

  --el-border-color: #e6eaf1;
  --el-border-color-light: #eff2f7;
  --el-border-color-lighter: #eff2f7;
  --el-border-color-extra-light: #f7f9fc;

  --el-text-color-primary: #0f172a;
  --el-text-color-regular: #334155;
  --el-text-color-secondary: #64748b;
  --el-text-color-placeholder: #94a3b8;
  --el-text-color-disabled: #cbd5e1;

  --el-border-radius-base: 10px;
  --el-border-radius-small: 8px;
  --el-border-radius-round: 999px;

  --el-font-size-base: 14px;
  --el-font-family: 'Inter', 'Noto Sans SC', -apple-system, BlinkMacSystemFont,
    'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

/* ============================================================
   全局重置
   ============================================================ */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
}

body {
  font-family: var(--el-font-family);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.6;
  color: var(--text-body);
  background-color: var(--bg-app);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

h1, h2, h3, h4, h5, h6 {
  font-size: inherit;
  font-weight: inherit;
  color: inherit;
}

a {
  color: inherit;
  text-decoration: none;
}

button,
input,
select,
textarea {
  font-family: inherit;
  font-size: inherit;
  color: inherit;
}

button {
  background: none;
  border: none;
  cursor: pointer;
}

ul, ol {
  list-style: none;
}

/* 数字用等宽字形，刷新时不跳动 */
.num {
  font-variant-numeric: tabular-nums;
}

::selection {
  background-color: var(--brand-100);
  color: var(--brand-700);
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: #d8dde6;
  border: 3px solid transparent;
  border-radius: var(--r-full);
  background-clip: content-box;
}

::-webkit-scrollbar-thumb:hover {
  background-color: #bcc3d0;
}

/* ============================================================
   Element Plus 细节修正
   ============================================================ */
.el-table {
  --el-table-border-color: var(--border-soft);
  --el-table-header-bg-color: var(--bg-subtle);
  --el-table-header-text-color: var(--text-muted);
  --el-table-row-hover-bg-color: var(--brand-50);
  font-size: 14px;
}

.el-table th.el-table__cell {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--text-muted);
  background-color: var(--bg-subtle) !important;
  padding: 12px 0 !important;
}

.el-table td.el-table__cell {
  padding: 14px 0 !important;
  border-bottom-color: var(--border-soft) !important;
}

.el-table .cell {
  padding: 0 18px;
}

/* 斑马纹更轻，融进白卡 */
.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: #fafbfd;
}

/* 去掉表格最外圈描边，让它融进卡片 */
.el-table::before,
.el-table__inner-wrapper::before {
  display: none;
}

.el-pagination {
  --el-pagination-font-size: 14px;
  font-weight: 500;
}

.el-pagination .el-pager li.is-active {
  font-weight: 600;
  background-color: var(--brand-600);
}

.el-pagination .el-pager li {
  border-radius: 8px;
}

.el-button {
  font-weight: 500;
  border-radius: var(--r-sm);
  /* 只过渡绘制类属性：transition: all 会连带布局属性一起过渡，容易抖动 */
  transition:
    background-color var(--motion-fast) var(--ease-standard),
    border-color var(--motion-fast) var(--ease-standard),
    color var(--motion-fast) var(--ease-standard),
    box-shadow var(--motion-fast) var(--ease-standard);
}

.el-button--primary {
  --el-button-bg-color: var(--brand-600);
  --el-button-border-color: var(--brand-600);
  --el-button-hover-bg-color: var(--brand-500);
  --el-button-hover-border-color: var(--brand-500);
  --el-button-active-bg-color: var(--brand-700);
  --el-button-active-border-color: var(--brand-700);
}

.el-button--danger.is-plain {
  --el-button-hover-text-color: #fff;
}

.el-input__wrapper,
.el-select__wrapper {
  border-radius: var(--r-sm) !important;
  box-shadow: 0 0 0 1px var(--border) inset !important;
  transition: box-shadow var(--dur) var(--ease);
}

.el-input__wrapper:hover,
.el-select__wrapper:hover {
  box-shadow: 0 0 0 1px #c9d2e0 inset !important;
}

.el-input__wrapper.is-focus,
.el-select__wrapper.is-focused {
  box-shadow: 0 0 0 1px var(--brand-500) inset, 0 0 0 3px var(--brand-100) !important;
}

.el-tag {
  border-radius: var(--r-full) !important;
  font-weight: 500;
  padding: 4px 12px !important;
  height: auto !important;
}

.el-dropdown-menu {
  border-radius: var(--r-md) !important;
  box-shadow: var(--shadow-md) !important;
  padding: 6px !important;
}

.el-dropdown-menu__item {
  border-radius: var(--r-sm) !important;
  padding: 9px 14px !important;
  font-size: 14px;
}

.el-message {
  border-radius: var(--r-sm);
}

.el-message-box {
  border-radius: var(--r-lg);
}

.el-notification {
  border-radius: var(--r-md);
  border-color: var(--border);
}

.el-loading-mask {
  background-color: rgba(255, 255, 255, 0.72);
}

/* 空状态 */
.el-empty__description p {
  color: var(--text-faint);
  font-size: 14px;
}

/* ============================================================
   入场工具类与无障碍降级
   ------------------------------------------------------------
   .reveal 是全局入场工具类：延迟由 utils/motion.js 的 revealStyle()
   以 --reveal-delay 注入，取代原先散落各处的 nth-child 硬编码。
   只动画 transform / opacity（合成层属性），不触发回流。

   填充模式用 backwards 而不是 both：动画结束后元素回到自身样式，
   否则动画的终态会一直覆盖 hover 的 transform，导致卡片 hover 位移失效。
   ============================================================ */
:root {
  --reveal-distance: 12px;
  --reveal-duration: var(--motion-slow);
}

.reveal {
  animation: reveal-rise var(--reveal-duration) var(--ease-enter) backwards;
  animation-delay: var(--reveal-delay, 0ms);
}

@keyframes reveal-rise {
  from {
    opacity: 0;
    transform: translate3d(0, var(--reveal-distance), 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

/* 窄屏减小位移幅度，避免出现"整页往上顶"的观感 */
@media (max-width: 900px) {
  :root {
    --reveal-distance: 8px;
  }
}

/* 系统要求减少动态效果：全局降到近乎瞬时。
   注意保留终止状态，元素不会停留在不可见状态。 */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-delay: 0ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    transition-delay: 0ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
