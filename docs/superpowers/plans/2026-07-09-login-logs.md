# 登录日志管理实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现登录日志的接收、存储和查询功能，包括后端 API 和前端页面。

**Architecture:** 后端采用模块化设计（API/Service/Schema 分离），前端组件化（Filter/Table/Pagination），严格遵循项目已有结构和 UI.md 设计规范。

**Tech Stack:** FastAPI + SQLAlchemy + Vue 3 + Element Plus + ECharts

---

## File Structure

### 后端文件
- `backend/app/schemas/logs_query.py` — 查询参数 Schema
- `backend/app/services/logs.py` — 日志业务逻辑
- `backend/app/api/logs.py` — 日志路由
- `backend/app/core/deps.py` — 添加 API Key 依赖（修改）
- `backend/app/core/config.py` — 添加 API_KEY（修改）
- `backend/app/main.py` — 注册路由（修改）

### 前端文件
- `frontend/src/api/logs.js` — 日志 API 封装
- `frontend/src/components/common/StatusTag.vue` — 状态标签组件
- `frontend/src/components/logs/LogPagination.vue` — 分页组件
- `frontend/src/components/logs/LogTable.vue` — 表格组件
- `frontend/src/components/logs/LogFilter.vue` — 筛选组件
- `frontend/src/views/LoginLogs.vue` — 日志列表页面
- `frontend/src/router/index.js` — 添加路由（修改）
- `frontend/src/layouts/MainLayout.vue` — 移除菜单 disabled（修改）

---

## Task 1: 创建查询参数 Schema

**Files:**
- Create: `backend/app/schemas/logs_query.py`

- [ ] **Step 1: Write the schema file**

```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.login_log import LoginLogResponse


class LogQueryParams(BaseModel):
    """日志查询参数"""
    username: Optional[str] = Field(None, description="模糊匹配用户名")
    ip_address: Optional[str] = None
    login_status: Optional[str] = Field(None, pattern="^(success|failure)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)

    @model_validator(mode='after')
    def check_time_range(self):
        """校验时间范围"""
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time 不能晚于 end_time")
        return self


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: list[LoginLogResponse]
    total: int
    skip: int
    limit: int
```

- [ ] **Step 2: Verify syntax**

Run: `cd backend && python -c "from app.schemas.logs_query import LogQueryParams; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/logs_query.py
git commit -m "feat: add log query schemas with validation"
```

---

## Task 2: 创建日志 Service 层

**Files:**
- Create: `backend/app/services/logs.py`

- [ ] **Step 1: Write the service file**

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate


def build_log_query(
    db: Session,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    login_status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """构建日志查询"""
    query = db.query(LoginLog)
    
    if username:
        query = query.filter(LoginLog.username.contains(username))
    if ip_address:
        query = query.filter(LoginLog.ip_address == ip_address)
    if login_status:
        query = query.filter(LoginLog.login_status == login_status)
    if start_time:
        query = query.filter(LoginLog.login_time >= start_time)
    if end_time:
        query = query.filter(LoginLog.login_time <= end_time)
    
    return query.order_by(desc(LoginLog.login_time))


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    **filters
) -> tuple[list[LoginLog], int]:
    """获取日志列表和总数"""
    query = build_log_query(db, **filters)
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    return logs, total


def create_log(db: Session, log_data: LoginLogCreate) -> LoginLog:
    """创建日志记录"""
    log = LoginLog(**log_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
```

- [ ] **Step 2: Verify syntax**

Run: `cd backend && python -c "from app.services.logs import create_log, get_logs; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/logs.py
git commit -m "feat: add log service layer with query builder"
```

---

## Task 3: 添加 API Key 依赖

**Files:**
- Modify: `backend/app/core/deps.py`

- [ ] **Step 1: Add verify_api_key function**

Add to end of `backend/app/core/deps.py`:

```python
from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """验证 API Key"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key
```

- [ ] **Step 2: Verify syntax**

Run: `cd backend && python -c "from app.core.deps import verify_api_key; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/deps.py
git commit -m "feat: add API key verification dependency"
```

---

## Task 4: 添加 API_KEY 配置

**Files:**
- Modify: `backend/app/core/config.py`

- [ ] **Step 1: Add API_KEY to Settings class**

Add after `ACCESS_TOKEN_EXPIRE_MINUTES`:

```python
API_KEY: str = "dev-api-key-change-in-production"
```

- [ ] **Step 2: Verify config loads**

Run: `cd backend && python -c "from app.core.config import settings; print(settings.API_KEY)"`
Expected: `dev-api-key-change-in-production`

- [ ] **Step 3: Commit**

```bash
git add backend/app/core/config.py
git commit -m "feat: add API_KEY config"
```

---

## Task 5: 创建日志 API 路由

**Files:**
- Create: `backend/app/api/logs.py`

- [ ] **Step 1: Write the API file**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_api_key
from app.models.user import User
from app.schemas.login_log import LoginLogCreate, LoginLogResponse
from app.schemas.logs_query import LogQueryParams, LogListResponse
from app.services.logs import create_log, get_logs

router = APIRouter()


@router.post("/logs", response_model=LoginLogResponse, status_code=201)
def receive_log(
    data: LoginLogCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """接收登录日志（校园系统调用）"""
    return create_log(db, data)


@router.get("/logs", response_model=LogListResponse)
def list_logs(
    params: LogQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询日志列表（管理员调用）"""
    logs, total = get_logs(
        db,
        skip=params.skip,
        limit=params.limit,
        username=params.username,
        ip_address=params.ip_address,
        login_status=params.login_status,
        start_time=params.start_time,
        end_time=params.end_time,
    )
    return {
        "items": logs,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
    }
```

- [ ] **Step 2: Verify syntax**

Run: `cd backend && python -c "from app.api.logs import router; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/logs.py
git commit -m "feat: add log API routes (receive and query)"
```

---

## Task 6: 注册日志路由到主应用

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Import and register logs router**

Add import:
```python
from app.api.logs import router as logs_router
```

Add after auth router:
```python
app.include_router(logs_router, prefix=settings.API_V1_PREFIX, tags=["日志"])
```

- [ ] **Step 2: Verify app starts**

Run: `cd backend && python -c "from app.main import app; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: register logs router"
```

---

## Task 7: 测试后端 API

**Files:**
- Create: `backend/tests/test_logs.py`

- [ ] **Step 1: Write tests**

```python
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_receive_log_with_invalid_api_key(client):
    resp = client.post("/api/logs", json={
        "username": "test",
        "login_time": "2026-07-09T14:30:00",
        "ip_address": "192.168.1.1",
        "user_agent": "Test",
        "login_status": "success"
    }, headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_list_logs_requires_auth(client):
    resp = client.get("/api/logs")
    assert resp.status_code == 401
```

- [ ] **Step 2: Run tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_logs.py -v`
Expected: 2 tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_logs.py
git commit -m "test: add log API tests"
```

---

## Task 8: 创建前端 API 封装

**Files:**
- Create: `frontend/src/api/logs.js`

- [ ] **Step 1: Write the API file**

```javascript
import api from './index'

export function getLogs(params) {
  return api.get('/api/logs', { params })
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/logs.js
git commit -m "feat: add logs API client"
```

---

## Task 9: 创建状态标签组件

**Files:**
- Create: `frontend/src/components/common/StatusTag.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <span class="status-tag" :class="statusClass">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  }
})

const statusClass = computed(() => ({
  'status-success': props.status === 'success',
  'status-failure': props.status === 'failure'
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
}

.status-success {
  background-color: #d1fae5;
  color: #10b981;
}

.status-failure {
  background-color: #fee2e2;
  color: #ef4444;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/common/StatusTag.vue
git commit -m "feat: add StatusTag component"
```

---

## Task 10: 创建分页组件

**Files:**
- Create: `frontend/src/components/logs/LogPagination.vue`

- [ ] **Step 1: Write the component**

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
  padding-top: 20px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/logs/LogPagination.vue
git commit -m "feat: add LogPagination component"
```

---

## Task 11: 创建表格组件

**Files:**
- Create: `frontend/src/components/logs/LogTable.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <el-table :data="logs" class="log-table">
    <el-table-column prop="username" label="用户名" min-width="120" />
    <el-table-column prop="login_time" label="登录时间" min-width="160">
      <template #default="{ row }">
        {{ formatDateTime(row.login_time) }}
      </template>
    </el-table-column>
    <el-table-column prop="ip_address" label="IP地址" min-width="140" />
    <el-table-column prop="login_status" label="状态" width="100">
      <template #default="{ row }">
        <StatusTag :status="row.login_status" />
      </template>
    </el-table-column>
    <el-table-column prop="location" label="位置" min-width="120" />
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
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/logs/LogTable.vue
git commit -m "feat: add LogTable component"
```

---

## Task 12: 创建筛选组件

**Files:**
- Create: `frontend/src/components/logs/LogFilter.vue`

- [ ] **Step 1: Write the component**

```vue
<template>
  <div class="filter-card">
    <div class="filter-row">
      <el-input
        v-model="filters.username"
        placeholder="用户名"
        clearable
        class="filter-input"
      />
      <el-input
        v-model="filters.ip_address"
        placeholder="IP地址"
        clearable
        class="filter-input"
      />
      <el-select
        v-model="filters.login_status"
        placeholder="登录状态"
        clearable
        class="filter-select"
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
        class="filter-date"
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
  background: #ffffff;
  border: 1px solid #e5e7eb;
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

.filter-input {
  width: 160px;
}

.filter-select {
  width: 140px;
}

.filter-date {
  width: 280px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/logs/LogFilter.vue
git commit -m "feat: add LogFilter component"
```

---

## Task 13: 创建日志列表页面

**Files:**
- Create: `frontend/src/views/LoginLogs.vue`

- [ ] **Step 1: Write the page**

```vue
<template>
  <div class="login-logs-page">
    <h1 class="page-title">登录日志</h1>
    
    <LogFilter @search="handleSearch" @reset="handleReset" />
    
    <div class="table-card">
      <LogTable :logs="logs" />
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
const currentFilters = ref({})

const fetchLogs = async () => {
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
  padding: 32px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
}

.table-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/LoginLogs.vue
git commit -m "feat: add LoginLogs page"
```

---

## Task 14: 添加路由

**Files:**
- Modify: `frontend/src/router/index.js`

- [ ] **Step 1: Add route**

Add to routes array:
```javascript
{
  path: '/login-logs',
  name: 'LoginLogs',
  component: () => import('../views/LoginLogs.vue'),
  meta: { requiresAuth: true }
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/router/index.js
git commit -m "feat: add login-logs route"
```

---

## Task 15: 启用侧边栏菜单

**Files:**
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Remove disabled from login-logs menu**

Find and remove `disabled` attribute from the login-logs menu item.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/layouts/MainLayout.vue
git commit -m "feat: enable login-logs menu"
```

---

## Task 16: 验证完整功能

- [ ] **Step 1: Start backend**

```bash
cd backend
$env:PYTHONPATH="."
uvicorn app.main:app --reload
```

- [ ] **Step 2: Start frontend**

```bash
cd frontend
npm run dev
```

- [ ] **Step 3: Test end-to-end**

1. 登录系统（admin/admin123）
2. 点击侧边栏"登录日志"
3. 验证列表加载
4. 测试筛选功能
5. 测试分页功能

- [ ] **Step 4: Final commit**

```bash
git commit -m "feat: complete login logs management (week 3)"
```

---

## Summary

**Total Tasks:** 16  
**Estimated Time:** 2-3 hours  
**Files Created:** 10  
**Files Modified:** 6

**Key Implementation Points:**
- API Key 认证用于日志接收，JWT 用于查询
- username 模糊匹配，其他字段精确匹配
- 时间范围校验防止 start_time > end_time
- 分页使用 skip/limit，前端组件使用 currentPage/pageSize
- 严格遵循 UI.md 设计规范