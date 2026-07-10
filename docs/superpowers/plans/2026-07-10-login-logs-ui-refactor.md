# 登录日志前端重构 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按照 `docs/UI.md` 规范重构登录日志页面的 5 个前端组件

**Architecture:** 每个组件独立修改，顺序执行。StatusTag → LogFilter → LogTable → LogPagination → LoginLogs（页面容器最后整合）。后端 API 不变。

**Tech Stack:** Vue 3 + Element Plus + CSS Variables（已在 `App.vue` 定义）

## Global Constraints

- 不修改后端任何文件
- 所有颜色值优先使用 `App.vue` 已定义的 CSS 变量（`--color-*`），其次从 `docs/UI.md` 取硬编码值
- 全大写表头（`text-transform: uppercase`，`letter-spacing: 0.05em`，`font-size: 12px`，`font-weight: 600`）
- 按钮圆角 8px，卡片圆角 12px，标签圆角 20px
- 输入框、下拉框、按钮统一高度 40px
- 日期选择器圆角覆盖为 8px

---

### Task 1: StatusTag — badge 样式

**Files:**
- Modify: `frontend/src/components/common/StatusTag.vue`

**Interfaces:**
- Consumes: `props.status: 'success' | 'failure'`（不变）
- Produces: 带背景色圆角 badge 的 `<span>`

- [ ] **Step 1: 重写 StatusTag 样式**

将纯色文字改为浅色背景 badge，色值直接从 UI 规范取：

```vue
<template>
  <span class="status-tag" :class="statusClass">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true }
})

const statusClass = computed(() => ({
  'status-tag--success': props.status === 'success',
  'status-tag--failure': props.status === 'failure'
}))

const label = computed(() => ({
  success: '成功',
  failure: '失败'
}[props.status] || props.status))
</script>

<style scoped>
.status-tag {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  line-height: 1;
}

.status-tag--success {
  background: #D1FAE5;
  color: #10B981;
}

.status-tag--failure {
  background: #FEE2E2;
  color: #EF4444;
}
</style>
```

- [ ] **Step 2: 确认无其他组件引用此组件导致样式断裂**

```bash
grep -r "StatusTag" frontend/src/ --include="*.vue" --include="*.js"
```

预期输出至少包含 `LogTable.vue` 和 `StatusTag.vue` 自身。

- [ ] **Step 3: Commit**

```bash
cd e:/实习
git add frontend/src/components/common/StatusTag.vue
git commit -m "refactor: StatusTag badge style per UI spec"
```

---

### Task 2: LogFilter — 筛选器卡片重构

**Files:**
- Modify: `frontend/src/components/logs/LogFilter.vue`

**Interfaces:**
- Consumes: `emit('search', params)`, `emit('reset')`（不变）
- Produces: 符合 UI 规范的筛选器卡片

- [ ] **Step 1: 重写 LogFilter.vue**

改动要点：
1. 移除 location 相关筛选
2. 所有输入框高度统一 40px（Element Plus 默认 size 即为 default）
3. 日期选择器圆角覆盖为 8px
4. 筛选器行支持 `flex-wrap: wrap` 响应式换行
5. 使用 CSS 变量替换硬编码色值

```vue
<template>
  <div class="filter-card">
    <div class="filter-row">
      <el-input
        v-model="filters.username"
        placeholder="用户名"
        clearable
        class="filter-item"
      />
      <el-input
        v-model="filters.ip_address"
        placeholder="IP地址"
        clearable
        class="filter-item"
      />
      <el-select
        v-model="filters.login_status"
        placeholder="登录状态"
        clearable
        class="filter-item filter-select"
      >
        <el-option label="成功" value="success" />
        <el-option label="失败" value="failure" />
      </el-select>
      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        class="filter-item filter-date"
      />
      <el-button type="primary" @click="handleSearch">
        <el-icon><Search /></el-icon>
        查询
      </el-button>
      <el-button @click="handleReset">重置</el-button>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { Search } from '@element-plus/icons-vue'

const emit = defineEmits(['search', 'reset'])

const filters = reactive({
  username: '',
  ip_address: '',
  login_status: '',
  dateRange: null
})

const handleSearch = () => {
  const params = {
    username: filters.username || undefined,
    ip_address: filters.ip_address || undefined,
    login_status: filters.login_status || undefined,
    start_time: filters.dateRange?.[0] ? `${filters.dateRange[0]}T00:00:00` : undefined,
    end_time: filters.dateRange?.[1] ? `${filters.dateRange[1]}T23:59:59` : undefined
  }
  emit('search', params)
}

const handleReset = () => {
  filters.username = ''
  filters.ip_address = ''
  filters.login_status = ''
  filters.dateRange = null
  emit('reset')
}
</script>

<style scoped>
.filter-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  gap: 16px;
  align-items: center;
  flex-wrap: wrap;
}

.filter-item {
  width: 160px;
}

.filter-select {
  width: 140px;
}

.filter-date {
  width: 280px;
}

/* 覆盖日期选择器圆角与按钮一致 */
.filter-date :deep(.el-input__wrapper) {
  border-radius: 8px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
cd e:/实习
git add frontend/src/components/logs/LogFilter.vue
git commit -m "refactor: LogFilter card style per UI spec"
```

---

### Task 3: LogTable — 表格重构，新增列

**Files:**
- Modify: `frontend/src/components/logs/LogTable.vue`

**Interfaces:**
- Consumes: `props.logs: Array`（不变）
- Produces: 带 ID、用户代理列、规范表头样式的表格

- [ ] **Step 1: 重写 LogTable.vue**

改动要点：
1. 新增 ID 列（80px）
2. 新增 user_agent 列（min-width 200px，flex:1，截断 + el-tooltip）
3. 表头背景 #F9FAFB，全大写样式
4. 分隔线：th 底部 #E5E7EB，td 底部 #F3F4F6
5. 启用横向滚动
6. 使用 CSS 变量

```vue
<template>
  <el-table
    :data="logs"
    class="log-table"
    stripe
    :header-cell-style="{
      backgroundColor: 'var(--color-bg)',
      color: 'var(--color-text-secondary)',
      fontWeight: 600,
      fontSize: '12px',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      borderBottomColor: 'var(--color-border)'
    }"
    :cell-style="{
      borderBottomColor: 'var(--color-border-light)'
    }"
  >
    <el-table-column prop="id" label="ID" width="80" />
    <el-table-column prop="username" label="用户名" min-width="120" />
    <el-table-column prop="login_status" label="状态" width="80">
      <template #default="{ row }">
        <StatusTag :status="row.login_status" />
      </template>
    </el-table-column>
    <el-table-column prop="login_time" label="登录时间" width="170">
      <template #default="{ row }">
        {{ formatDateTime(row.login_time) }}
      </template>
    </el-table-column>
    <el-table-column prop="ip_address" label="IP地址" width="140" />
    <el-table-column label="用户代理" min-width="200" flex="1">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.user_agent"
          :content="row.user_agent"
          effect="dark"
          placement="top"
          :show-after="300"
        >
          <span class="ua-text">{{ row.user_agent }}</span>
        </el-tooltip>
        <span v-else class="ua-empty">-</span>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import StatusTag from '../common/StatusTag.vue'

defineProps({
  logs: {
    type: Array,
    required: true
  }
})

const formatDateTime = (isoString) => {
  if (!isoString) return '-'
  const date = new Date(isoString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '-')
}
</script>

<style scoped>
.log-table {
  width: 100%;
}

.ua-text {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
}

.ua-empty {
  color: var(--color-text-tertiary);
}
</style>
```

- [ ] **Step 2: Commit**

```bash
cd e:/实习
git add frontend/src/components/logs/LogTable.vue
git commit -m "refactor: LogTable add ID and user_agent columns, table header style per UI spec"
```

---

### Task 4: LogPagination — 微调

**Files:**
- Modify: `frontend/src/components/logs/LogPagination.vue`

**Interfaces:**
- Consumes: `props.total, skip, limit`（不变），`emit('change', skip, limit)`（不变）
- Produces: 逻辑不变，样式微调

- [ ] **Step 1: 微调 LogPagination.vue**

当前样式已基本符合规范，仅调整 `padding-top` 使其与表格卡片内部间距协调：

```vue
<template>
  <div class="pagination-wrapper">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
      @change="handleChange"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  total: { type: Number, required: true },
  skip: { type: Number, default: 0 },
  limit: { type: Number, default: 50 }
})

const emit = defineEmits(['change'])

const currentPage = computed({
  get: () => Math.floor(props.skip / props.limit) + 1,
  set: (val) => {
    const skip = (val - 1) * pageSize.value
    emit('change', skip, pageSize.value)
  }
})

const pageSize = computed({
  get: () => props.limit,
  set: (val) => {
    emit('change', 0, val)
  }
})

const handleChange = () => {
  const skip = (currentPage.value - 1) * pageSize.value
  emit('change', skip, pageSize.value)
}
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
cd e:/实习
git add frontend/src/components/logs/LogPagination.vue
git commit -m "refactor: LogPagination adjust spacing for table card integration"
```

---

### Task 5: LoginLogs — 页面容器重构

**Files:**
- Modify: `frontend/src/views/LoginLogs.vue`

**Interfaces:**
- Consumes: `LogFilter`, `LogTable`, `LogPagination` 组件（来自 Task 1-4）
- Produces: 完整的登录日志页面

- [ ] **Step 1: 重写 LoginLogs.vue**

改动要点：
1. 使用 CSS 变量替换硬编码色值
2. 添加 `v-loading` 加载状态
3. 添加 `el-empty` 空数据状态
4. 表格卡片添加 `box-shadow: 0 1px 3px rgba(0,0,0,0.05)`
5. 分页放在表格卡片内部

```vue
<template>
  <div class="login-logs-page">
    <LogFilter @search="handleSearch" @reset="handleReset" />

    <div class="table-card" v-loading="loading">
      <LogTable v-if="logs.length > 0" :logs="logs" />
      <el-empty v-else description="暂无登录日志" />

      <LogPagination
        :total="total"
        :skip="skip"
        :limit="limit"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LogFilter from '../components/logs/LogFilter.vue'
import LogTable from '../components/logs/LogTable.vue'
import LogPagination from '../components/logs/LogPagination.vue'
import { getLogs } from '../api/logs'

const logs = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(50)
const loading = ref(false)
const currentFilters = ref({})

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await getLogs({
      skip: skip.value,
      limit: limit.value,
      ...currentFilters.value
    })
    logs.value = res.items
    total.value = res.total
  } catch (err) {
    console.error('Failed to fetch logs:', err)
    logs.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = (params) => {
  skip.value = 0
  currentFilters.value = params
  fetchLogs()
}

const handleReset = () => {
  skip.value = 0
  currentFilters.value = {}
  fetchLogs()
}

const handlePageChange = (newSkip, newLimit) => {
  skip.value = newSkip
  limit.value = newLimit
  fetchLogs()
}

onMounted(fetchLogs)
</script>

<style scoped>
.login-logs-page {
  padding: 0;
}

.table-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 空状态文字颜色与 Caption 层级一致 */
.table-card :deep(.el-empty__description p) {
  color: #9CA3AF;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
cd e:/实习
git add frontend/src/views/LoginLogs.vue
git commit -m "refactor: LoginLogs page container with loading, empty state, card shadow"
```

---

### Task 6: 最终验证

- [ ] **Step 1: 确认前端构建无报错**

```bash
cd e:/实习/frontend
npm run build 2>&1
```

预期：构建成功，无错误输出。

- [ ] **Step 2: 确认 lint 通过**

```bash
cd e:/实习/frontend
npm run lint 2>&1
```

预期：无错误或仅 warnings。

- [ ] **Step 3: 确认所有修改文件已提交**

```bash
cd e:/实习
git status
```

预期：工作区干净，无未提交文件。

- [ ] **Step 4: 确认最终提交**

```bash
git log --oneline -6
```

预期：显示 5 个功能提交 + 可能 1 个设计文档提交。