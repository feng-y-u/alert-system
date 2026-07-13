# 第六周前端联调 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现告警列表页（替换占位页）并给 Dashboard 新增三张告警维度 ECharts 图表，新增后端 `GET /api/stats/alerts` 接口支撑图表数据。

**Architecture:** 复用 LoginLogs 页的 Filter/Table/Pagination 三件套模式构建告警列表；Dashboard 图表 ECharts 配置内联不抽组件；后端在 `stats.py` 内新增第二个路由返回告警趋势/类型分布/级别分布聚合数据。前端 API 层新增 `api/alerts.js` 和 `api/stats.js` 两个文件。

**Tech Stack:** FastAPI + SQLAlchemy（后端）、Vue 3 + Element Plus + ECharts + Pinia + Axios（前端）、pytest（后端测试）

**Spec:** `docs/superpowers/specs/2026-07-13-week6-frontend-integration-design.md`

---

## 文件结构

### 后端

| 文件 | 动作 | 责任 |
|------|------|------|
| `backend/app/api/stats.py` | 修改 | 新增 `GET /stats/alerts` 路由，返回告警维度统计 |
| `backend/tests/test_alert_stats.py` | 新增 | 告警统计接口测试 |

### 前端

| 文件 | 动作 | 责任 |
|------|------|------|
| `frontend/src/api/alerts.js` | 新增 | `getAlerts` / `updateAlertStatus` 两个 API 函数 |
| `frontend/src/api/stats.js` | 新增 | `getAlertStats` API 函数 |
| `frontend/src/components/common/StatusTag.vue` | 修改 | 扩展 `type` prop 支持四种 tag 类型 |
| `frontend/src/components/alerts/AlertFilter.vue` | 新增 | status/severity/username 三项筛选 |
| `frontend/src/components/alerts/AlertTable.vue` | 新增 | 告警表格 + 行内状态变更下拉 |
| `frontend/src/components/alerts/AlertPagination.vue` | 新增 | 分页（复制 LogPagination） |
| `frontend/src/views/Alerts.vue` | 重写 | 占位页 → 容器页 |
| `frontend/src/views/Dashboard.vue` | 修改 | 新增告警区三张图表 |
| `frontend/src/layouts/MainLayout.vue` | 修改 | 侧边栏告警项启用 |

---

## Task 1: 后端 GET /api/stats/alerts 接口

**Files:**
- Modify: `backend/app/api/stats.py`
- Test: `backend/tests/test_alert_stats.py`

- [ ] **Step 1: 写失败测试 — 未登录返回 401**

创建 `backend/tests/test_alert_stats.py`：

```python
"""告警统计接口测试"""


def test_alert_stats_requires_auth(client):
    """未登录访问 /api/stats/alerts 返回 401"""
    resp = client.get("/api/stats/alerts")
    assert resp.status_code == 401
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && pytest tests/test_alert_stats.py::test_alert_stats_requires_auth -v`
Expected: FAIL — 路由不存在，返回 404 而非 401

- [ ] **Step 3: 写登录 helper 并扩展测试**

替换 `backend/tests/test_alert_stats.py` 全部内容：

```python
"""告警统计接口测试"""

from app.core.security import create_access_token


def _auth_headers():
    """返回 admin 用户的 Bearer 头（假设 seed.py 已创建 admin）"""
    token = create_access_token(data={"sub": "1"})
    return {"Authorization": f"Bearer {token}"}


def test_alert_stats_requires_auth(client):
    """未登录访问 /api/stats/alerts 返回 401"""
    resp = client.get("/api/stats/alerts")
    assert resp.status_code == 401


def test_alert_stats_structure(client):
    """登录后返回包含三个聚合 key 的结构"""
    resp = client.get("/api/stats/alerts", headers=_auth_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert "alertTrend" in data
    assert "typeDist" in data
    assert "severityDist" in data


def test_alert_stats_trend_length_default(client):
    """默认 days=7，alertTrend 长度为 7"""
    resp = client.get("/api/stats/alerts", headers=_auth_headers())
    data = resp.json()
    assert len(data["alertTrend"]) == 7


def test_alert_stats_trend_length_30(client):
    """days=30 时 alertTrend 长度为 30"""
    resp = client.get("/api/stats/alerts?days=30", headers=_auth_headers())
    data = resp.json()
    assert len(data["alertTrend"]) == 30
```

- [ ] **Step 4: 运行测试确认全部失败**

Run: `cd backend && pytest tests/test_alert_stats.py -v`
Expected: 4 个测试全部 FAIL（路由 404）

- [ ] **Step 5: 实现后端路由**

修改 `backend/app/api/stats.py`，在文件顶部 import 区加 `func`，在现有 `get_stats` 函数之后追加新路由。

修改第 1 行 import：
```python
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
```

在文件末尾追加：

```python
@router.get("/stats/alerts")
def get_alert_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取告警维度统计数据（趋势/类型分布/级别分布）"""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=days)

    # 告警趋势：逐日统计
    trend = []
    for i in range(days - 1, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.query(Alert).filter(
            Alert.created_at >= day_start,
            Alert.created_at < day_end,
        ).count()
        trend.append({
            "date": day_start.strftime("%m-%d"),
            "count": count,
        })

    # 类型分布
    type_rows = db.query(Alert.alert_type, func.count()).filter(
        Alert.created_at >= window_start,
    ).group_by(Alert.alert_type).all()
    type_dist = [{"name": t, "value": c} for t, c in type_rows]

    # 级别分布
    severity_rows = db.query(Alert.severity, func.count()).filter(
        Alert.created_at >= window_start,
    ).group_by(Alert.severity).all()
    severity_dist = [{"name": s, "value": c} for s, c in severity_rows]

    return {
        "alertTrend": trend,
        "typeDist": type_dist,
        "severityDist": severity_dist,
    }
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd backend && pytest tests/test_alert_stats.py -v`
Expected: 4 个测试 PASS

注意：`test_alert_stats_requires_auth` 在路由存在后应返回 401（无 Bearer 头）。若 `client` fixture 走真实 MySQL 且 admin 用户不存在，登录相关测试会因 `sub: "1"` 对应用户不存在而 401 —— 需先跑 `python scripts/seed.py` 创建 admin。

- [ ] **Step 7: 运行全部后端测试确认无回归**

Run: `cd backend && pytest -v`
Expected: 所有测试 PASS（test_health / test_security / test_detection / test_alert_stats）

- [ ] **Step 8: 格式化**

Run: `cd backend && black .`
Expected: 格式化通过，无报错

- [ ] **Step 9: 提交**

```bash
git add backend/app/api/stats.py backend/tests/test_alert_stats.py
git commit -m "feat: 新增 GET /api/stats/alerts 告警统计接口"
```

---

## Task 2: 前端 API 层

**Files:**
- Create: `frontend/src/api/alerts.js`
- Create: `frontend/src/api/stats.js`

- [ ] **Step 1: 创建 api/alerts.js**

创建 `frontend/src/api/alerts.js`：

```js
import api from './index'

export function getAlerts(params) {
  return api.get('/api/alerts', { params })
}

export function updateAlertStatus(alertId, status) {
  return api.put(`/api/alerts/${alertId}`, { status })
}
```

- [ ] **Step 2: 创建 api/stats.js**

创建 `frontend/src/api/stats.js`：

```js
import api from './index'

export function getAlertStats(days = 7) {
  return api.get('/api/stats/alerts', { params: { days } })
}
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/alerts.js frontend/src/api/stats.js
git commit -m "feat: 新增前端 alerts/stats API 模块"
```

---

## Task 3: StatusTag 扩展支持告警类型

**Files:**
- Modify: `frontend/src/components/common/StatusTag.vue`

- [ ] **Step 1: 重写 StatusTag.vue 支持四种 type**

替换 `frontend/src/components/common/StatusTag.vue` 全部内容：

```vue
<template>
  <span class="status-tag" :class="classObj">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: 'login'
  }
})

const labelMap = {
  login: { success: '成功', failure: '失败' },
  alert_status: { pending: '待处理', acknowledged: '已确认', resolved: '已处理' },
  alert_severity: { low: '低', medium: '中', high: '高' },
  alert_type: { frequency: '频率异常', device: '设备异常' }
}

const classMap = {
  login: { success: 'status-tag--success', failure: 'status-tag--failure' },
  alert_status: {
    pending: 'status-tag--warning',
    acknowledged: 'status-tag--info',
    resolved: 'status-tag--success'
  },
  alert_severity: {
    low: 'status-tag--info',
    medium: 'status-tag--warning',
    high: 'status-tag--failure'
  },
  alert_type: {
    frequency: 'status-tag--neutral',
    device: 'status-tag--neutral'
  }
}

const label = computed(() => labelMap[props.type]?.[props.status] || props.status)
const classObj = computed(() => ({
  [classMap[props.type]?.[props.status] || '']: true
}))
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
  background: var(--color-success-light);
  color: var(--color-success);
}

.status-tag--failure {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.status-tag--warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.status-tag--info {
  background: #dbeafe;
  color: #3b82f6;
}

.status-tag--neutral {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/common/StatusTag.vue
git commit -m "feat: StatusTag 扩展支持告警状态/级别/类型"
```

---

## Task 4: AlertFilter 组件

**Files:**
- Create: `frontend/src/components/alerts/AlertFilter.vue`

- [ ] **Step 1: 创建 AlertFilter.vue**

创建 `frontend/src/components/alerts/AlertFilter.vue`：

```vue
<template>
  <div class="filter-card">
    <div class="filter-row">
      <el-select
        v-model="filters.status"
        placeholder="告警状态"
        clearable
        class="filter-item filter-select"
      >
        <el-option label="待处理" value="pending" />
        <el-option label="已确认" value="acknowledged" />
        <el-option label="已处理" value="resolved" />
      </el-select>
      <el-select
        v-model="filters.severity"
        placeholder="严重级别"
        clearable
        class="filter-item filter-select"
      >
        <el-option label="低" value="low" />
        <el-option label="中" value="medium" />
        <el-option label="高" value="high" />
      </el-select>
      <el-input
        v-model="filters.username"
        placeholder="用户名"
        clearable
        class="filter-item"
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
  status: '',
  severity: '',
  username: ''
})

const handleSearch = () => {
  const params = {
    status: filters.status || undefined,
    severity: filters.severity || undefined,
    username: filters.username || undefined
  }
  emit('search', params)
}

const handleReset = () => {
  filters.status = ''
  filters.severity = ''
  filters.username = ''
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
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/alerts/AlertFilter.vue
git commit -m "feat: 新增 AlertFilter 筛选组件"
```

---

## Task 5: AlertPagination 组件

**Files:**
- Create: `frontend/src/components/alerts/AlertPagination.vue`

- [ ] **Step 1: 创建 AlertPagination.vue（复制 LogPagination 逻辑）**

创建 `frontend/src/components/alerts/AlertPagination.vue`：

```vue
<template>
  <div class="pagination-wrapper">
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next"
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
</script>

<style scoped>
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/alerts/AlertPagination.vue
git commit -m "feat: 新增 AlertPagination 分页组件"
```

---

## Task 6: AlertTable 组件

**Files:**
- Create: `frontend/src/components/alerts/AlertTable.vue`

- [ ] **Step 1: 创建 AlertTable.vue**

创建 `frontend/src/components/alerts/AlertTable.vue`：

```vue
<template>
  <el-table
    :data="alerts"
    class="alert-table"
    stripe
    :header-cell-style="() => ({
      backgroundColor: 'var(--color-bg)',
      color: 'var(--color-text-secondary)',
      fontWeight: 600,
      fontSize: '12px',
      textTransform: 'uppercase',
      letterSpacing: '0.05em',
      borderBottomColor: 'var(--color-border)',
      whiteSpace: 'nowrap',
    })"
    :cell-style="{
      borderBottomColor: 'var(--color-border-light)',
      whiteSpace: 'nowrap'
    }"
  >
    <el-table-column prop="id" label="ID" min-width="60" />
    <el-table-column prop="username" label="用户名" min-width="100" />
    <el-table-column label="类型" min-width="100">
      <template #default="{ row }">
        <StatusTag :status="row.alert_type" type="alert_type" />
      </template>
    </el-table-column>
    <el-table-column label="级别" min-width="80" align="center">
      <template #default="{ row }">
        <StatusTag :status="row.severity" type="alert_severity" />
      </template>
    </el-table-column>
    <el-table-column label="状态" min-width="100" align="center">
      <template #default="{ row }">
        <StatusTag :status="row.status" type="alert_status" />
      </template>
    </el-table-column>
    <el-table-column label="告警内容" min-width="200">
      <template #default="{ row }">
        <el-tooltip
          v-if="row.alert_message"
          :content="row.alert_message"
          effect="dark"
          placement="top"
          :show-after="300"
        >
          <span class="msg-text">{{ row.alert_message }}</span>
        </el-tooltip>
        <span v-else class="msg-empty">-</span>
      </template>
    </el-table-column>
    <el-table-column label="创建时间" min-width="150">
      <template #default="{ row }">
        {{ formatDateTime(row.created_at) }}
      </template>
    </el-table-column>
    <el-table-column label="操作" min-width="80" align="center">
      <template #default="{ row }">
        <el-dropdown trigger="click" @command="(cmd) => emit('status-change', row.id, cmd)">
          <el-button text>
            <el-icon><MoreFilled /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pending" :disabled="row.status === 'pending'">
                标记为待处理
              </el-dropdown-item>
              <el-dropdown-item command="acknowledged" :disabled="row.status === 'acknowledged'">
                标记为已确认
              </el-dropdown-item>
              <el-dropdown-item command="resolved" :disabled="row.status === 'resolved'">
                标记为已处理
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { MoreFilled } from '@element-plus/icons-vue'
import StatusTag from '../common/StatusTag.vue'

defineProps({
  alerts: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['status-change'])

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
.alert-table {
  width: 100%;
  overflow-x: auto;
}

.msg-text {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: default;
  vertical-align: middle;
}

.msg-empty {
  color: var(--color-text-tertiary);
}
</style>

<style>
.alert-table .el-table__body td.el-table__cell .cell,
.alert-table .el-table__header th.el-table__cell .cell {
  white-space: nowrap !important;
  word-break: keep-all !important;
}
</style>
```

- [ ] **Step 2: 提交**

```bash
git add frontend/src/components/alerts/AlertTable.vue
git commit -m "feat: 新增 AlertTable 表格组件（含行内状态变更）"
```

---

## Task 7: Alerts.vue 容器页 + MainLayout 启用

**Files:**
- Modify: `frontend/src/views/Alerts.vue`
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: 重写 Alerts.vue**

替换 `frontend/src/views/Alerts.vue` 全部内容：

```vue
<template>
  <div class="alerts-page">
    <AlertFilter @search="handleSearch" @reset="handleReset" />

    <div class="table-card" v-loading="loading">
      <AlertTable
        v-if="alerts.length > 0"
        :alerts="alerts"
        @status-change="handleStatusChange"
      />
      <el-empty v-else description="暂无告警" />

      <AlertPagination
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
import { ElMessage } from 'element-plus'
import AlertFilter from '../components/alerts/AlertFilter.vue'
import AlertTable from '../components/alerts/AlertTable.vue'
import AlertPagination from '../components/alerts/AlertPagination.vue'
import { getAlerts, updateAlertStatus } from '../api/alerts'

const alerts = ref([])
const total = ref(0)
const skip = ref(0)
const limit = ref(50)
const loading = ref(false)
const currentFilters = ref({})

const fetchAlerts = async () => {
  loading.value = true
  try {
    const res = await getAlerts({
      skip: skip.value,
      limit: limit.value,
      ...currentFilters.value
    })
    alerts.value = res.items
    total.value = res.total
  } catch (err) {
    console.error('Failed to fetch alerts:', err)
    alerts.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = (params) => {
  skip.value = 0
  currentFilters.value = params
  fetchAlerts()
}

const handleReset = () => {
  skip.value = 0
  currentFilters.value = {}
  fetchAlerts()
}

const handlePageChange = (newSkip, newLimit) => {
  skip.value = newSkip
  limit.value = newLimit
  fetchAlerts()
}

const handleStatusChange = async (alertId, newStatus) => {
  try {
    await updateAlertStatus(alertId, newStatus)
    ElMessage.success('告警状态已更新')
    fetchAlerts()
  } catch (err) {
    console.error('Failed to update alert status:', err)
    ElMessage.error('更新告警状态失败')
  }
}

onMounted(fetchAlerts)
</script>

<style scoped>
.alerts-page {
  padding: 0;
}

.table-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.table-card :deep(.el-empty__description p) {
  color: #9CA3AF;
}
</style>
```

- [ ] **Step 2: 修改 MainLayout.vue 启用告警菜单项**

修改 `frontend/src/layouts/MainLayout.vue` 第 105 行：

将：
```js
{ path: '/alerts', label: '告警列表', icon: WarningFilled, disabled: true },
```

改为：
```js
{ path: '/alerts', label: '告警列表', icon: WarningFilled, disabled: false },
```

- [ ] **Step 3: 启动前后端手动验证**

```bash
docker-compose up -d
cd backend && uvicorn app.main:app --reload --port 8001
cd frontend && npm run dev
```

浏览器访问 http://localhost:5173 ，登录 admin/admin123，验证：
- [ ] 侧边栏「告警列表」可点击，不再灰显
- [ ] 空数据时显示「暂无告警」
- [ ] 有数据时表格渲染，列与字段对应
- [ ] status / severity / username 筛选 → 表格刷新
- [ ] 分页切换 → 表格刷新
- [ ] 行内下拉切换状态 → 列表刷新 + ElMessage 成功提示
- [ ] 下拉中当前状态项 disabled

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/Alerts.vue frontend/src/layouts/MainLayout.vue
git commit -m "feat: 告警列表页联调完成 + 侧边栏启用"
```

---

## Task 8: Dashboard 图表增强

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: 修改 Dashboard.vue script — 新增 import 与 ref**

修改 `frontend/src/views/Dashboard.vue`，在 `<script setup>` 块内：

将第 96 行 `import api from '../api'` 之后追加：

```js
import { getAlertStats } from '../api/stats'
```

在现有 ref 声明区（第 112 行 `const trend = ref([])` 之后）追加：

```js
const alertTrend = ref([])
const typeDist = ref([])
const severityDist = ref([])

const alertTrendRef = ref(null)
const typeDistRef = ref(null)
const severityDistRef = ref(null)
let alertTrendChart = null
let typeDistChart = null
let severityDistChart = null
```

在现有 `let chartInstance = null`（第 115 行）保持不动。

- [ ] **Step 2: 改造 refreshData 函数 — 并发获取 + 渲染告警图表**

将 `refreshData` 函数（第 121-211 行）整体替换为：

```js
const refreshData = async () => {
  try {
    const days = timeRange.value === 'week' ? 7 : 30
    const [loginRes, alertRes] = await Promise.all([
      api.get('/api/stats', { params: { days } }),
      getAlertStats(days),
    ])
    stats.todayLogins = loginRes.todayLogins
    stats.pendingAlerts = loginRes.pendingAlerts
    stats.activeUsers = loginRes.activeUsers
    trend.value = loginRes.loginTrend || []
    alertTrend.value = alertRes.alertTrend || []
    typeDist.value = alertRes.typeDist || []
    severityDist.value = alertRes.severityDist || []

    // 销毁所有旧图表
    chartInstance?.dispose()
    alertTrendChart?.dispose()
    typeDistChart?.dispose()
    severityDistChart?.dispose()
    chartInstance = null
    alertTrendChart = null
    typeDistChart = null
    severityDistChart = null

    // 登录趋势图（现有逻辑保留）
    if (chartRef.value) {
      chartRef.value.style.opacity = '0'
      chartInstance = echarts.init(chartRef.value)
      chartInstance.setOption({
        animationDuration: 2500,
        animationEasing: 'cubicOut',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#111827' },
          padding: [12, 16],
        },
        grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: trend.value.map(t => t.date),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        series: [{
          type: 'line',
          data: trend.value.map(t => t.count),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          animationDuration: 2500,
          animationEasing: 'cubicOut',
          animationDelay: 400,
          lineStyle: {
            width: 3,
            color: '#111827',
            shadowColor: 'rgba(17, 24, 39, 0.3)',
            shadowBlur: 10,
            shadowOffsetY: 5,
          },
          itemStyle: { color: '#111827', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            opacity: 0.8,
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(17, 24, 39, 0.2)' },
                { offset: 1, color: 'rgba(17, 24, 39, 0)' },
              ],
            },
          },
        }],
      })
      requestAnimationFrame(() => {
        chartRef.value.style.opacity = '1'
      })
    }

    // 告警趋势折线图
    if (alertTrendRef.value) {
      alertTrendChart = echarts.init(alertTrendRef.value)
      alertTrendChart.setOption({
        animationDuration: 2500,
        animationEasing: 'cubicOut',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e5e7eb',
          borderWidth: 1,
          textStyle: { color: '#111827' },
          padding: [12, 16],
        },
        grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: alertTrend.value.map(t => t.date),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        series: [{
          type: 'line',
          data: alertTrend.value.map(t => t.count),
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: {
            width: 3,
            color: '#F59E0B',
            shadowColor: 'rgba(245, 158, 11, 0.3)',
            shadowBlur: 10,
            shadowOffsetY: 5,
          },
          itemStyle: { color: '#F59E0B', borderWidth: 2, borderColor: '#fff' },
          areaStyle: {
            opacity: 0.8,
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(245, 158, 11, 0.2)' },
                { offset: 1, color: 'rgba(245, 158, 11, 0)' },
              ],
            },
          },
        }],
      })
    }

    // 告警类型分布环形图
    if (typeDistRef.value) {
      typeDistChart = echarts.init(typeDistRef.value)
      const typeNameMap = { frequency: '频率异常', device: '设备异常' }
      typeDistChart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { bottom: 0, textStyle: { color: '#6b7280', fontSize: 12 } },
        series: [{
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '45%'],
          avoidLabelOverlap: false,
          label: { show: false },
          labelLine: { show: false },
          data: typeDist.value.map((item, i) => ({
            name: typeNameMap[item.name] || item.name,
            value: item.value,
            itemStyle: { color: ['#111827', '#F59E0B'][i % 2] },
          })),
        }],
      })
    }

    // 严重级别分布柱状图
    if (severityDistRef.value) {
      severityDistChart = echarts.init(severityDistRef.value)
      const severityNameMap = { low: '低', medium: '中', high: '高' }
      const severityColorMap = { low: '#3B82F6', medium: '#F59E0B', high: '#EF4444' }
      severityDistChart.setOption({
        tooltip: { trigger: 'axis' },
        grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
        xAxis: {
          type: 'category',
          data: severityDist.value.map(s => severityNameMap[s.name] || s.name),
          axisLine: { lineStyle: { color: '#e5e7eb' } },
          axisTick: { show: false },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        yAxis: {
          type: 'value',
          splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
          axisLabel: { color: '#6b7280', fontSize: 12 },
        },
        series: [{
          type: 'bar',
          data: severityDist.value.map(s => ({
            value: s.value,
            itemStyle: { color: severityColorMap[s.name] || '#111827' },
          })),
          barWidth: '40%',
          itemStyle: { borderRadius: [6, 6, 0, 0] },
        }],
      })
    }
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}
```

- [ ] **Step 3: 修改 onUnmounted — 销毁所有图表实例**

将 `onUnmounted`（第 222-224 行）替换为：

```js
onUnmounted(() => {
  chartInstance?.dispose()
  alertTrendChart?.dispose()
  typeDistChart?.dispose()
  severityDistChart?.dispose()
})
```

- [ ] **Step 4: 修改 template — 插入告警分析区**

在 template 中，找到 `<!-- 快捷操作 -->` 注释（第 66 行）之前，插入告警分析区：

```html
    <!-- 告警分析区 -->
    <div class="chart-section">
      <div class="section-header">
        <h2 class="section-title">告警趋势</h2>
      </div>
      <div ref="alertTrendRef" class="chart-container"></div>
    </div>

    <div class="alert-charts-grid">
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">告警类型分布</h2>
        </div>
        <div ref="typeDistRef" class="chart-container-small"></div>
      </div>

      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">严重级别分布</h2>
        </div>
        <div ref="severityDistRef" class="chart-container-small"></div>
      </div>
    </div>
```

插入位置：在现有 `chart-section`（登录趋势图）的 `</div>` 之后、`<!-- 快捷操作 -->` 之前。

- [ ] **Step 5: 追加告警图表 CSS**

在 `<style scoped>` 块末尾（现有 `@media (max-width: 768px)` 之前）追加：

```css
/* === 告警图表区 === */
.alert-charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-container-small {
  height: 280px;
}

@media (max-width: 1024px) {
  .alert-charts-grid {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 6: 启动前后端手动验证**

```bash
docker-compose up -d
cd backend && uvicorn app.main:app --reload --port 8001
cd frontend && npm run dev
```

浏览器访问 http://localhost:5173 ，登录后进入仪表盘，验证：
- [ ] 切换近7天/近30天，四张图全部刷新
- [ ] 告警趋势折线图渲染，x 轴日期数量与 days 一致
- [ ] 类型分布环形图 legend 显示「频率异常/设备异常」
- [ ] 级别分布柱状图 x 轴显示「低/中/高」
- [ ] 空数据时图表不报错
- [ ] 页面切换/刷新无 ECharts 实例泄漏（控制台无报错）

- [ ] **Step 7: 提交**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "feat: Dashboard 新增告警趋势/类型分布/级别分布三张图表"
```

---

## Task 9: 最终验证与文档更新

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/DESIGN.md`

- [ ] **Step 1: 运行全部后端测试**

Run: `cd backend && pytest -v`
Expected: 所有测试 PASS

- [ ] **Step 2: 后端格式化**

Run: `cd backend && black .`
Expected: 无报错

- [ ] **Step 3: 更新 CLAUDE.md 开发计划状态**

修改 `CLAUDE.md` 第 135 行：

将：
```
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ❌ |
```

改为：
```
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ✅ |
```

- [ ] **Step 4: 更新 DESIGN.md 开发计划状态**

修改 `docs/DESIGN.md` 第 54 行：

将：
```
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ❌ |
```

改为：
```
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ✅ |
```

- [ ] **Step 5: 提交**

```bash
git add CLAUDE.md docs/DESIGN.md
git commit -m "docs: 标记第六周完成"
```
