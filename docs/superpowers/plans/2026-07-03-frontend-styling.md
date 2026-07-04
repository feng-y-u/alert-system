# 前端页面风格实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于已确认的 "B — 极简白+浅灰" 设计方案，将前端页面的全局样式、MainLayout、Login 页和 Dashboard 页的风格从 Element Plus 默认主题更新为简约大气的自定义设计系统。

**Architecture:** 通过 CSS 变量覆盖 Element Plus 主题 + scoped style 覆盖各组件，无需改动组件逻辑代码，仅修改样式层。字体通过 Google Fonts 引入 Inter + Noto Sans SC。

**Tech Stack:** Vue 3 + Element Plus + ECharts + Inter/Noto Sans SC

## Global Constraints

- 所有按钮文字与正文统一：`14px` / `font-weight: 400`（不额外加粗）
- 字体栈：`'Inter', 'Noto Sans SC', -apple-system, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif`
- 颜色值严格使用设计规范中的色值，不得近似替代
- 卡片统一使用白底 + 边框 `#e5e7eb 1px` + `border-radius: 10px`，无默认阴影
- 所有修改在现有文件上增量完成，不重构逻辑

---

### Task 1: 全局样式变量覆盖 & 字体引入

**Files:**
- Modify: `frontend/index.html` — 添加 Google Fonts 引入
- Modify: `frontend/src/App.vue` — 添加 Element Plus 主题变量覆盖 + 全局基础样式
- Create: (无) — 变量直接写在 App.vue 的 `<style>` 中

**Interfaces:**
- Consumes: 无
- Produces: 全局 CSS 变量 `--el-color-primary` 等，全站字体栈生效

---

- [ ] **Step 1: 在 `index.html` 中添加字体引入**

向 `<head>` 中添加：

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

- [ ] **Step 2: 更新 `App.vue` — 添加 Element Plus 主题变量覆盖**

将 `<style>` 中的全局 `*` 和 `body` 样式替换为完整的设计 Token 覆盖：

```html
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
```

- [ ] **Step 3: 验证**

```bash
cd frontend && npm run dev
```

确认页面正常启动，字体变为 Inter/Noto Sans SC，Element Plus 组件颜色已更新为设计色值。

- [ ] **Step 4: 提交**

```bash
git add frontend/index.html frontend/src/App.vue
git commit -m "style: add global theme tokens and font imports"
```

---

### Task 2: MainLayout 侧边栏 & 顶栏样式更新

**Files:**
- Modify: `frontend/src/layouts/MainLayout.vue`

**Interfaces:**
- Consumes: 全局 CSS 变量（Task 1）
- Produces: 深蓝侧栏 + 白色顶栏布局

---

- [ ] **Step 1: 替换 MainLayout 侧边栏样式**

将 `<el-aside>` 的背景色从 `#001529` 改为 `#1a1a2e`，`<el-menu>` 的背景色同步更新。
将 `.logo` 改为带蓝色图标 Logo 的样式：

```html
<!-- 模板部分：Logo 区域改为蓝色图标 + 品牌名 -->
<div class="sidebar-header">
  <div class="logo-icon">S</div>
  <span class="logo-text" v-show="!isCollapse">校园监测平台</span>
</div>
```

```css
/* 侧边栏容器 */
.el-aside {
  background-color: #1a1a2e !important;
  transition: width 0.3s;
  overflow: hidden;
}

/* Logo 头部 */
.sidebar-header {
  height: 56px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.logo-icon {
  width: 28px;
  height: 28px;
  background: #2563eb;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.logo-text {
  color: white;
  font-size: 15px;
  font-weight: 500;
  white-space: nowrap;
}
```

- [ ] **Step 2: 覆盖 Element Plus Menu 组件样式**

在 `<style>` 中添加深色主题的 Menu 覆盖：

```css
/* 侧栏菜单容器 */
.el-menu {
  border-right: none !important;
  background-color: #1a1a2e !important;
  padding: 8px 8px;
}

/* 菜单项 */
.el-menu-item {
  height: 40px !important;
  line-height: 40px !important;
  border-radius: 8px !important;
  margin-bottom: 2px;
  padding: 0 12px !important;
  font-size: 14px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.7) !important;
  background-color: transparent !important;
}

.el-menu-item:hover {
  background-color: rgba(255, 255, 255, 0.05) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

/* 活跃菜单项 */
.el-menu-item.is-active {
  color: #60a5fa !important;
  background-color: rgba(37, 99, 235, 0.15) !important;
}

/* 菜单图标 */
.el-menu-item .el-icon {
  color: rgba(255, 255, 255, 0.5) !important;
  margin-right: 10px;
}

.el-menu-item.is-active .el-icon {
  color: #60a5fa !important;
}

/* 折叠状态 */
.el-menu--collapse .el-menu-item {
  padding: 0 12px !important;
  justify-content: center;
}

.el-menu--collapse .el-menu-item .el-icon {
  margin-right: 0;
}
```

- [ ] **Step 3: 重写顶栏样式**

将 `.el-header` 改为白色背景，重新设计顶部布局：

```css
/* 顶栏 */
.el-header {
  height: 56px !important;
  background-color: #ffffff !important;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px !important;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 折叠按钮 */
.collapse-btn {
  font-size: 14px;
  color: #9ca3af;
  cursor: pointer;
  border: none;
  background: none;
  padding: 4px;
}

/* 面包屑文字（当前路由名） */
.breadcrumb {
  font-size: 14px;
  color: #6b7280;
}

/* 用户区域 */
.user-dropdown {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #6b7280;
}

.user-avatar {
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  color: #374151;
}
```

- [ ] **Step 4: 更新模板中的顶栏部分**

将 `<el-header>` 内的 HTML 更新为：

```html
<el-header>
  <div class="header-left">
    <button class="collapse-btn" @click="toggleCollapse">
      {{ isCollapse ? '☰' : '☰' }}
    </button>
    <span class="breadcrumb">{{ routeName }}</span>
  </div>
  <div class="header-right">
    <span>{{ username }}</span>
    <div class="user-avatar">👤</div>
  </div>
</el-header>
```

对应在 script 中添加：

```javascript
const routeName = computed(() => {
  const map = { '/': '仪表盘', '/login-logs': '登录日志', '/alerts': '告警列表' }
  return map[route.path] || ''
})
```

- [ ] **Step 5: 更新内容区背景**

将 `.el-main` 的背景色改为 `#f8f9fa`：

```css
.el-main {
  background-color: #f8f9fa;
  padding: 24px;
  overflow-y: auto;
}
```

- [ ] **Step 6: 验证**

```bash
cd frontend && npm run dev
```

确认：
- 侧栏背景为深蓝 `#1a1a2e`，Logo 区域有蓝色 `S` 图标
- 活跃菜单项蓝色高亮，非活跃项半透明白色文字
- 顶栏白色背景，左侧折叠按钮+面包屑，右侧用户名+圆形头像
- 折叠动画平滑

- [ ] **Step 7: 提交**

```bash
git add frontend/src/layouts/MainLayout.vue
git commit -m "style: update sidebar and header to match design system"
```

---

### Task 3: Login 页面样式优化

**Files:**
- Modify: `frontend/src/views/Login.vue`

**Interfaces:**
- Consumes: 全局 CSS 变量（Task 1）
- Produces: 符合设计规范的登录页面

---

- [ ] **Step 1: 替换 Login 页面模板**

将整个 `<template>` 替换为：

```html
<template>
  <div class="login-container">
    <div class="login-card">
      <!-- Logo -->
      <div class="login-header">
        <div class="login-logo">S</div>
        <h1 class="login-title">管理员登录</h1>
        <p class="login-subtitle">校园账号异常登录监测平台</p>
      </div>

      <!-- Error message -->
      <div v-if="error" class="login-error">
        <span>⚠️</span>
        <span>{{ error }}</span>
      </div>

      <!-- Form -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @keyup.enter="handleLogin"
        class="login-form"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入管理员用户名"
            :prefix-icon="User"
            :disabled="loading"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            :prefix-icon="Lock"
            :disabled="loading"
            show-password
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            :loading="loading"
            :disabled="loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ loading ? '正在验证...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <!-- Footer -->
      <p class="login-footer">仅限管理员登录 · 版权所有 © 2026</p>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 更新脚本部分**

替换 `<script setup>` 为（保留原有登录逻辑，增加表单验证规则）：

```javascript
<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref(null)

const form = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
  ],
}

const loading = ref(false)
const error = ref('')

const handleLogin = async () => {
  if (!formRef.value) return

  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  error.value = ''

  try {
    await authStore.login(form.username, form.password)
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || '用户名或密码错误，请重新输入'
  } finally {
    loading.value = false
  }
}
</script>
```

- [ ] **Step 3: 替换样式**

将 `<style scoped>` 整体替换为：

```css
<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8f9fa;
  padding: 24px;
}

.login-card {
  width: 400px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 40px 36px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* Header */
.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-logo {
  width: 48px;
  height: 48px;
  background: #1a1a2e;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 20px;
  font-weight: 700;
  margin: 0 auto 16px;
}

.login-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.login-subtitle {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

/* Error banner */
.login-error {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #991b1b;
  margin-bottom: 20px;
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 12px;
}

/* 输入框样式覆盖 */
.login-form :deep(.el-input__wrapper) {
  height: 40px;
  border-radius: 8px;
  box-shadow: 0 0 0 1px #d1d5db inset !important;
  padding: 0 12px;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #2563eb inset !important;
}

.login-form :deep(.el-input__inner) {
  font-size: 14px;
  color: #111827;
  height: 40px;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #9ca3af;
}

.login-form :deep(.el-input__prefix) {
  font-size: 14px;
  color: #9ca3af;
}

/* Login button */
.login-btn {
  width: 100%;
  height: 40px !important;
  font-size: 14px !important;
  font-weight: 400 !important;
  border-radius: 8px !important;
  margin-top: 4px;
}

/* Footer */
.login-footer {
  text-align: center;
  font-size: 12px;
  color: #9ca3af;
  margin-top: 24px;
}
</style>
```

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run dev
```

登录页面应显示：
- 居中白卡 + 极细边框 + 微阴影
- 蓝色「S」Logo +「管理员登录」+ 平台名称
- 用户名/密码输入框带图标前缀、placeholder
- 空字段提交显示红色提示，登录中按钮显示 loading
- API 错误时显示红色错误条

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Login.vue
git commit -m "style: redesign login page with new design system"
```

---

### Task 4: Dashboard 页面优化

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

**Interfaces:**
- Consumes: 全局 CSS 变量（Task 1）
- Produces: 符合设计规范的 Dashboard 页面，含 4 张统计卡片、ECharts 趋势图、告警类型分布、最近告警表格

---

- [ ] **Step 1: 更新模板 — 页面标题 + 4 列统计卡片**

替换 `<template>` 中的统计卡片部分：

```html
<template>
  <div class="dashboard">
    <!-- Page header -->
    <div class="page-header">
      <h2 class="page-title">仪表盘</h2>
      <p class="page-desc">实时掌握校园账号登录状态</p>
    </div>

    <!-- Stat cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">今日登录</div>
        <div class="stat-value">{{ stats.todayLogins }}</div>
        <div class="stat-meta">LoginLog · login_time 今日</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">失败次数</div>
        <div class="stat-value warn-color">{{ stats.failedLogins }}</div>
        <div class="stat-meta">LoginLog · login_status=failure</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">待处理告警</div>
        <div class="stat-value danger-color">{{ stats.pendingAlerts }}</div>
        <div class="stat-meta">Alert · status=pending</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">告警处理率</div>
        <div class="stat-value success-color">{{ stats.resolveRate }}%</div>
        <div class="stat-meta">resolved / 总告警数</div>
      </div>
    </div>

    <!-- Chart row -->
    <div class="charts-grid">
      <div class="chart-card-wide">
        <div class="chart-header">
          <span class="chart-title">登录趋势（近 7 天）</span>
          <div class="chart-tabs">
            <span class="tab" :class="{ active: trendRange === 'today' }" @click="trendRange = 'today'">今日</span>
            <span class="tab" :class="{ active: trendRange === '7d' }" @click="trendRange = '7d'">7 天</span>
            <span class="tab" :class="{ active: trendRange === '30d' }" @click="trendRange = '30d'">30 天</span>
          </div>
        </div>
        <div ref="trendChartRef" class="chart-body"></div>
      </div>
      <div class="chart-card-narrow">
        <div class="chart-header">
          <span class="chart-title">告警类型分布</span>
        </div>
        <div class="alert-distribution">
          <div class="dist-item">
            <div class="dist-label">
              <span>频率异常</span>
              <span class="dist-pct">{{ alertDistribution.frequency }}%</span>
            </div>
            <div class="dist-bar">
              <div class="dist-fill danger" :style="{ width: alertDistribution.frequency + '%' }"></div>
            </div>
          </div>
          <div class="dist-item">
            <div class="dist-label">
              <span>设备异常</span>
              <span class="dist-pct">{{ alertDistribution.device }}%</span>
            </div>
            <div class="dist-bar">
              <div class="dist-fill warning" :style="{ width: alertDistribution.device + '%' }"></div>
            </div>
          </div>
          <div class="dist-item">
            <div class="dist-label">
              <span>位置异常</span>
              <span class="dist-pct">{{ alertDistribution.location }}%</span>
            </div>
            <div class="dist-bar">
              <div class="dist-fill primary" :style="{ width: alertDistribution.location + '%' }"></div>
            </div>
          </div>
        </div>
        <div class="chart-footer-note">Alert · alert_type 枚举</div>
      </div>
    </div>

    <!-- Recent alerts table -->
    <div class="table-card">
      <div class="table-card-header">
        <span class="table-card-title">最近告警</span>
        <el-button type="primary" size="small" @click="$router.push('/alerts')">查看全部</el-button>
      </div>
      <el-table :data="recentAlerts" style="width: 100%" empty-text="暂无告警">
        <el-table-column prop="created_at" label="告警时间" width="110" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="alert_type" label="告警类型" width="110">
          <template #default="{ row }">
            <span :class="['pill', 'pill-' + row.alert_type]">{{ alertTypeLabel(row.alert_type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="alert_message" label="告警消息" min-width="180" />
        <el-table-column prop="severity" label="严重程度" width="100">
          <template #default="{ row }">
            <span :class="['pill', 'pill-severity-' + row.severity]">{{ row.severity }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <span :class="['pill', 'pill-status-' + row.status]">{{ statusLabel(row.status) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 更新脚本 — 响应式数据 + ECharts**

将 `<script setup>` 替换为：

```javascript
<script setup>
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'

const stats = reactive({
  todayLogins: 1284,
  failedLogins: 37,
  pendingAlerts: 23,
  resolveRate: 86,
})

const trendRange = ref('7d')
const alertDistribution = reactive({
  frequency: 45,
  device: 30,
  location: 25,
})

const recentAlerts = reactive([
  { created_at: '14:23:12', username: 'zhangsan', alert_type: 'frequency', alert_message: '5 分钟内登录失败 6 次', severity: 'high', status: 'pending' },
  { created_at: '13:47:05', username: 'lisi', alert_type: 'location', alert_message: '非校园 IP 登录（美国）', severity: 'high', status: 'acknowledged' },
  { created_at: '11:02:34', username: 'wangwu', alert_type: 'device', alert_message: '从未知设备首次登录', severity: 'medium', status: 'resolved' },
])

function alertTypeLabel(type) {
  const map = { frequency: '频率异常', device: '设备异常', location: '位置异常' }
  return map[type] || type
}

function statusLabel(status) {
  const map = { pending: 'pending', acknowledged: 'acknowledged', resolved: 'resolved' }
  return map[status] || status
}

// ECharts trend chart
const trendChartRef = ref(null)
let trendChartInstance = null

onMounted(() => {
  if (trendChartRef.value) {
    trendChartInstance = echarts.init(trendChartRef.value)
    trendChartInstance.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'line' },
      },
      grid: {
        left: 20,
        right: 20,
        top: 20,
        bottom: 20,
        containLabel: false,
      },
      xAxis: {
        type: 'category',
        data: ['06/27', '06/28', '06/29', '06/30', '07/01', '07/02', '07/03'],
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#9ca3af',
          fontSize: 12,
        },
      },
      yAxis: {
        type: 'value',
        splitLine: {
          lineStyle: { color: '#f3f4f6', type: 'dashed' },
        },
        axisLabel: {
          color: '#9ca3af',
          fontSize: 12,
        },
        axisLine: { show: false },
        axisTick: { show: false },
      },
      series: [
        {
          type: 'line',
          data: [156, 172, 198, 165, 210, 185, 192],
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            color: '#2563eb',
            width: 2,
          },
          itemStyle: {
            color: '#2563eb',
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(37, 99, 235, 0.1)' },
              { offset: 1, color: 'rgba(37, 99, 235, 0)' },
            ]),
          },
        },
        {
          type: 'line',
          data: [200, 200, 200, 200, 200, 200, 200],
          symbol: 'none',
          lineStyle: {
            color: '#f59e0b',
            width: 1,
            type: 'dashed',
          },
          label: {
            show: true,
            formatter: '阈值',
            color: '#f59e0b',
            fontSize: 10,
            position: 'end',
          },
        },
      ],
    })
  }
})

onUnmounted(() => {
  trendChartInstance?.dispose()
})
</script>
```

- [ ] **Step 3: 替换样式**

将整个 `<style scoped>` 替换为：

```css
<style scoped>
.dashboard {
  max-width: 1200px;
}

/* Page header */
.page-header {
  margin-bottom: 24px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.page-desc {
  font-size: 13px;
  color: #6b7280;
  margin-top: 4px;
}

/* Stat cards grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px;
}

.stat-label {
  font-size: 13px;
  color: #6b7280;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #111827;
}

.stat-value.warn-color {
  color: #f59e0b;
}

.stat-value.danger-color {
  color: #ef4444;
}

.stat-value.success-color {
  color: #10b981;
}

.stat-meta {
  font-size: 13px;
  color: #6b7280;
  margin-top: 8px;
}

/* Charts grid */
.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}

.chart-card-wide,
.chart-card-narrow {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.chart-title {
  font-size: 16px;
  font-weight: 500;
  color: #111827;
}

.chart-tabs {
  display: flex;
  gap: 8px;
}

.tab {
  font-size: 13px;
  color: #6b7280;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.tab.active {
  color: #2563eb;
  font-weight: 500;
}

.chart-body {
  height: 200px;
}

/* Alert distribution bars */
.alert-distribution {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-top: 8px;
}

.dist-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dist-label {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #6b7280;
}

.dist-pct {
  color: #111827;
  font-weight: 500;
}

.dist-bar {
  height: 6px;
  background: #f3f4f6;
  border-radius: 3px;
  overflow: hidden;
}

.dist-fill {
  height: 6px;
  border-radius: 3px;
  transition: width 0.3s;
}

.dist-fill.danger {
  background: #ef4444;
}

.dist-fill.warning {
  background: #f59e0b;
}

.dist-fill.primary {
  background: #3b82f6;
}

.chart-footer-note {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
}

/* Table card */
.table-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 20px;
}

.table-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.table-card-title {
  font-size: 16px;
  font-weight: 500;
  color: #111827;
}

/* Status pills */
.pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 400;
}

/* Alert type pills */
.pill-frequency {
  background: #fef3c7;
  color: #92400e;
}

.pill-device {
  background: #e0e7ff;
  color: #3730a3;
}

.pill-location {
  background: #fee2e2;
  color: #991b1b;
}

/* Severity pills */
.pill-severity-high {
  background: #fee2e2;
  color: #991b1b;
}

.pill-severity-medium {
  background: #fef3c7;
  color: #92400e;
}

.pill-severity-low {
  background: #dcfce7;
  color: #166534;
}

/* Status pills */
.pill-status-pending {
  background: #fef3c7;
  color: #92400e;
}

.pill-status-acknowledged {
  background: #e0e7ff;
  color: #3730a3;
}

.pill-status-resolved {
  background: #dcfce7;
  color: #166534;
}

/* Responsive: collapse to 2 columns on medium screens */
@media (max-width: 900px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

> 注意：由于当前后端只实现了认证功能（第 2 周），LoginLog 和 Alert 数据尚不存在。Dashboard 的统计数据使用**演示占位数据**，后续接入真实 API 时替换为后端查询。

- [ ] **Step 4: 验证**

```bash
cd frontend && npm run dev
```

确认：
- 4 列统计卡片显示正确的标签和默认值
- ECharts 趋势图渲染正常，含渐变区域和虚线阈值
- 右侧告警类型分布进度条颜色正确
- 最近告警表格含 6 列，状态标签使用胶囊形 Pill
- 响应式布局在窄屏下折叠为 2 列

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "style: redesign dashboard with stats cards, charts, and alerts table"
```

---

## 自检清单

- [x] **Spec coverage**: 设计文档的所有要求均已映射到对应的 Task：
  - 2.1 色彩体系 → Task 1 (CSS 变量)
  - 2.2 字体体系 → Task 1 (字体引入 + 全局 font-family)
  - 2.3 间距体系 → Task 1 (CSS 变量 × 各组件 padding)
  - 3.1 MainLayout → Task 2
  - 3.2 登录页 → Task 3
  - 3.3 Dashboard → Task 4
  - 4.1-4.5 组件规范 → Task 1 (全局) +各 Task (scoped 覆盖)
  - 5.1-5.2 全局样式 → Task 1
  - 5.4 字体引入 → Task 1

- [x] **Placeholder scan**: 无 "TBD"、"TODO"、"implement later" — 所有代码都是完整可用的

- [x] **Type consistency**: 组件名、API 名、css class 名在跨 Task 引用时保持一致

- [x] **Scope check**: 专注于 4 个 Task 的样式层修改，不涉及后端 API 或业务逻辑变动