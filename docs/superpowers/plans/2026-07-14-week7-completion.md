# 第7周功能完善 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成第7周三大模块——SSE 实时告警推送、前端错误处理加固（L1+L2）、Dashboard 图表组件化优化。

**Architecture:** 后端 Celery 检测任务发布告警事件到 Redis pub/sub → FastAPI SSE 端点订阅并推送给前端 → Pinia notificationStore 管理角标与 toast。前端 Axios 拦截器捕获 5xx/403/429/网络错误弹全局 toast，各页面补 loading/error/empty 三态。Dashboard 的 4 个内联 ECharts 图表抽成独立组件 + time range 防抖。

**Tech Stack:** FastAPI StreamingResponse + Redis pub/sub + Celery + Vue 3 + Pinia + Element Plus + ECharts + lodash-es

---

> **Note:** 三个模块（SSE、错误处理、优化）互不依赖，可并行推进。但建议先做完 Dashboard 优化再改 Dashboard 的错误处理态，避免对同一文件反复合并。

---

### Task 1: 告警生成后发布 Redis pub/sub 事件

**Files:**
- Modify: `backend/app/tasks/detection.py:1-13`

- [ ] **Step 1: 添加 `import json` 和 `_publish_alert_event` 辅助函数**

在 `detection.py` 顶部 `from app.tasks.email import send_alert_email` 后面插入 `import json`，然后在 `def get_last_check_time()` 之前插入 `_publish_alert_event` 函数：

```python
import json


def _publish_alert_event(alert):
    """发布告警事件到 Redis pub/sub"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.publish("alerts", json.dumps({
            "alert_id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "username": alert.username,
        }))
    except Exception:
        pass  # pub/sub 失败不影响告警生成主流程
```

- [ ] **Step 2: 在实时检测任务中调用 `_publish_alert_event`**

`detect_anomaly_for_log` 函数中，频率告警生成后加一行 `_publish_alert_event(freq_alert)`，设备告警生成后加一行 `_publish_alert_event(device_alert)`：

```python
        # 频率检测
        freq_alert = detect_frequency_anomaly(db, log.username, log_id)
        if freq_alert:
            results.append(f"Frequency alert created: {freq_alert.id}")
            send_alert_email.delay(freq_alert.id)
            _publish_alert_event(freq_alert)

        # 设备检测
        device_alert = detect_device_anomaly(db, log.username, log_id)
        if device_alert:
            results.append(f"Device alert created: {device_alert.id}")
            send_alert_email.delay(device_alert.id)
            _publish_alert_event(device_alert)
```

- [ ] **Step 3: 在定时检测任务中调用 `_publish_alert_event`**

`run_anomaly_detection` 函数中同样在频率和设备检测告警生成后各加一行：

```python
            # 频率检测
            freq_alert = detect_frequency_anomaly(db, username)
            if freq_alert:
                total_alerts += 1
                send_alert_email.delay(freq_alert.id)
                _publish_alert_event(freq_alert)

            # 设备检测
            device_alert = detect_device_anomaly(db, username)
            if device_alert:
                total_alerts += 1
                send_alert_email.delay(device_alert.id)
                _publish_alert_event(device_alert)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/tasks/detection.py
git commit -m "feat: 检测告警生成后发布 Redis pub/sub 事件"
```

---

### Task 2: 创建 SSE 端点

**Files:**
- Create: `backend/app/api/notifications.py`

- [ ] **Step 1: 创建 `backend/app/api/notifications.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from starlette.responses import StreamingResponse
from sqlalchemy.orm import Session

import redis
from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

router = APIRouter()


def _get_user_from_token(token: str, db: Session) -> User:
    """从 query token 解析当前用户，失败抛 401"""
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token 中缺少用户信息")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="用户已被禁用")

    return user


@router.get("/notifications/stream")
async def stream_notifications(
    token: str = Query(..., description="JWT Token"),
    db: Session = Depends(get_db),
):
    """SSE 端点：实时推送新告警通知"""
    _get_user_from_token(token, db)

    r = redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    pubsub.subscribe("alerts")

    async def event_generator():
        try:
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                else:
                    yield f": heartbeat\n\n"
        except Exception:
            pass
        finally:
            pubsub.unsubscribe("alerts")
            pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/notifications.py
git commit -m "feat: 新增 SSE 端 /api/notifications/stream"
```

---

### Task 3: 注册 notifications router

**Files:**
- Modify: `backend/app/main.py:5-9,31`

- [ ] **Step 1: 在 `main.py` 添加 import 和 include_router**

```python
from app.api.notifications import router as notifications_router
```

然后在现有 `app.include_router(alerts_router, ...)` 之后添加：

```python
app.include_router(notifications_router, prefix=settings.API_V1_PREFIX, tags=["实时通知"])
```

- [ ] **Step 2: 验证后端启动正常**

```bash
cd backend
python -c "from app.main import app; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: 注册 notifications router"
```

---

### Task 4: Axios 拦截器扩展全局错误处理

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 修改响应拦截器**

```js
import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 10000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status

    if (status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
      return Promise.reject(error)
    }

    if (status >= 500) {
      ElMessage.error('服务器异常，请稍后重试')
    } else if (status === 403) {
      ElMessage.error('无权限访问')
    } else if (status === 429) {
      ElMessage.warning('请求过于频繁，请稍后再试')
    } else if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络')
    }

    return Promise.reject(error)
  }
)

export default api
```

- [ ] **Step 2: 验证**

```bash
cd frontend
```
启动前端后，停掉后端口令，访问任意页面执行操作，应看到 toast "网络连接失败，请检查网络"。

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "feat: Axios 拦截器新增 5xx/403/429/网络错误全局 toast"
```

---

### Task 5: 创建 LoginTrendChart.vue

**Files:**
- Create: `frontend/src/components/charts/LoginTrendChart.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

const buildOption = (data) => ({
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
    data: data.map(t => t.date),
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
    data: data.map(t => t.count),
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

const render = () => {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption(props.data))
}

onMounted(() => {
  chartRef.value.style.opacity = '0'
  render()
  requestAnimationFrame(() => {
    if (chartRef.value) chartRef.value.style.opacity = '1'
  })
})

watch(() => props.data, () => {
  if (chartRef.value) chartRef.value.style.opacity = '0'
  render()
  requestAnimationFrame(() => {
    if (chartRef.value) chartRef.value.style.opacity = '1'
  })
})

onUnmounted(() => {
  chart?.dispose()
})
</script>

<style scoped>
.chart-container {
  height: 320px;
  transition: opacity 0.8s ease;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/charts/LoginTrendChart.vue
git commit -m "feat: 新增 LoginTrendChart 组件"
```

---

### Task 6: 创建 AlertTrendChart.vue

**Files:**
- Create: `frontend/src/components/charts/AlertTrendChart.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

const buildOption = (data) => ({
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
    data: data.map(t => t.date),
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
    data: data.map(t => t.count),
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

const render = () => {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption(props.data))
}

onMounted(render)
watch(() => props.data, render)
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart-container {
  height: 320px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/charts/AlertTrendChart.vue
git commit -m "feat: 新增 AlertTrendChart 组件"
```

---

### Task 7: 创建 TypeDistChart.vue

**Files:**
- Create: `frontend/src/components/charts/TypeDistChart.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

const typeNameMap = { frequency: '频率异常', device: '设备异常' }

const buildOption = (data) => ({
  tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
  legend: { bottom: 0, textStyle: { color: '#6b7280', fontSize: 12 } },
  series: [{
    type: 'pie',
    radius: ['45%', '70%'],
    center: ['50%', '45%'],
    avoidLabelOverlap: false,
    label: { show: false },
    labelLine: { show: false },
    data: data.map((item, i) => ({
      name: typeNameMap[item.name] || item.name,
      value: item.value,
      itemStyle: { color: ['#111827', '#F59E0B'][i % 2] },
    })),
  }],
})

const render = () => {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption(props.data))
}

onMounted(render)
watch(() => props.data, render)
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart-container {
  height: 280px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/charts/TypeDistChart.vue
git commit -m "feat: 新增 TypeDistChart 组件"
```

---

### Task 8: 创建 SeverityDistChart.vue

**Files:**
- Create: `frontend/src/components/charts/SeverityDistChart.vue`

- [ ] **Step 1: 创建组件**

```vue
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

const severityNameMap = { low: '低', medium: '中', high: '高' }
const severityColorMap = { low: '#3B82F6', medium: '#F59E0B', high: '#EF4444' }

const buildOption = (data) => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 0, right: 0, top: 20, bottom: 0, containLabel: true },
  xAxis: {
    type: 'category',
    data: data.map(s => severityNameMap[s.name] || s.name),
    axisLine: { lineStyle: { color: '#e5e7eb' } },
    axisTick: { show: false },
    axisLabel: { color: '#6b7280', fontSize: 12 },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#f3f4f6', type: 'dashed' } },
    axisLabel: { color: '#6b7280', fontSize: 12 },
    minInterval: 1,
  },
  series: [{
    type: 'bar',
    data: data.map(s => ({
      value: s.value,
      itemStyle: { color: severityColorMap[s.name] || '#111827' },
    })),
    barWidth: '40%',
    itemStyle: { borderRadius: [6, 6, 0, 0] },
  }],
})

const render = () => {
  if (!chartRef.value) return
  chart?.dispose()
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption(props.data))
}

onMounted(render)
watch(() => props.data, render)
onUnmounted(() => chart?.dispose())
</script>

<style scoped>
.chart-container {
  height: 280px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/charts/SeverityDistChart.vue
git commit -m "feat: 新增 SeverityDistChart 组件"
```

---

### Task 9: 重构 Dashboard.vue

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

本次修改三合一：① 替换内联图表为子组件引用 ② time range 防抖 ③ loading/error/empty 状态。

- [ ] **Step 1: 重写 Dashboard.vue**

```vue
<template>
  <div class="dashboard" v-loading="loading">
    <!-- 错误状态 -->
    <div v-if="error" class="error-placeholder">
      <p>数据加载失败，请稍后重试</p>
      <el-button type="primary" @click="refreshData">重试</el-button>
    </div>

    <template v-else>
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">今日登录</span>
            <div class="stat-badge success">
              <el-icon><TrendCharts /></el-icon>
            </div>
          </div>
          <div class="stat-value">{{ formatNumber(stats.todayLogins) }}</div>
          <div class="stat-footer">
            <span class="stat-trend positive">+12%</span>
            <span class="stat-compare">较昨日</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">待处理告警</span>
            <div class="stat-badge warning">
              <el-icon><Warning /></el-icon>
            </div>
          </div>
          <div class="stat-value" :class="{ 'text-warning': stats.pendingAlerts > 0 }">
            {{ stats.pendingAlerts }}
          </div>
          <div class="stat-footer">
            <span class="stat-trend" :class="stats.pendingAlerts > 10 ? 'negative' : 'neutral'">
              {{ stats.pendingAlerts > 10 ? '↑' : '→' }}
            </span>
            <span class="stat-compare">需关注</span>
          </div>
        </div>

        <div class="stat-card">
          <div class="stat-header">
            <span class="stat-label">活跃用户</span>
            <div class="stat-badge info">
              <el-icon><User /></el-icon>
            </div>
          </div>
          <div class="stat-value">{{ formatNumber(stats.activeUsers) }}</div>
          <div class="stat-footer">
            <span class="stat-trend positive">+5%</span>
            <span class="stat-compare">较昨日</span>
          </div>
        </div>
      </div>

      <!-- 登录趋势 -->
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">登录趋势</h2>
          <div class="section-actions">
            <el-radio-group v-model="timeRange" size="small">
              <el-radio-button value="week">近7天</el-radio-button>
              <el-radio-button value="month">近30天</el-radio-button>
            </el-radio-group>
          </div>
        </div>
        <LoginTrendChart v-if="trend.length > 0" :data="trend" />
        <div v-else class="empty-chart">暂无登录数据</div>
      </div>

      <!-- 告警趋势 -->
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">告警趋势</h2>
        </div>
        <AlertTrendChart v-if="alertTrend.length > 0" :data="alertTrend" />
        <div v-else class="empty-chart">暂无告警数据</div>
      </div>

      <div class="alert-charts-grid">
        <div class="chart-section">
          <div class="section-header">
            <h2 class="section-title">告警类型分布</h2>
          </div>
          <TypeDistChart v-if="typeDist.length > 0" :data="typeDist" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>

        <div class="chart-section">
          <div class="section-header">
            <h2 class="section-title">严重级别分布</h2>
          </div>
          <SeverityDistChart v-if="severityDist.length > 0" :data="severityDist" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>
      </div>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <h3 class="section-title">快捷操作</h3>
        <div class="actions-grid">
          <button class="action-card" disabled>
            <div class="action-icon">
              <el-icon><Document /></el-icon>
            </div>
            <span class="action-label">查看日志</span>
          </button>
          <button class="action-card" disabled>
            <div class="action-icon">
              <el-icon><WarningFilled /></el-icon>
            </div>
            <span class="action-label">处理告警</span>
          </button>
          <button class="action-card" @click="refreshData">
            <div class="action-icon primary">
              <el-icon><Refresh /></el-icon>
            </div>
            <span class="action-label">刷新数据</span>
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { debounce } from 'lodash-es'
import api from '../api'
import { getAlertStats } from '../api/stats'
import LoginTrendChart from '../components/charts/LoginTrendChart.vue'
import AlertTrendChart from '../components/charts/AlertTrendChart.vue'
import TypeDistChart from '../components/charts/TypeDistChart.vue'
import SeverityDistChart from '../components/charts/SeverityDistChart.vue'
import {
  TrendCharts,
  Warning,
  User,
  Document,
  WarningFilled,
  Refresh
} from '@element-plus/icons-vue'

const stats = reactive({
  todayLogins: 0,
  pendingAlerts: 0,
  activeUsers: 0,
})

const trend = ref([])
const alertTrend = ref([])
const typeDist = ref([])
const severityDist = ref([])
const timeRange = ref('week')
const loading = ref(false)
const error = ref(false)

const formatNumber = (num) => {
  return num.toLocaleString('zh-CN')
}

const refreshData = async () => {
  loading.value = true
  error.value = false
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
  } catch (err) {
    console.error('Failed to load stats:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

const debouncedRefresh = debounce(refreshData, 300)

onMounted(() => {
  refreshData()
})

watch(timeRange, () => {
  debouncedRefresh()
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* === 错误占位 === */
.error-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 80px 0;
}

.error-placeholder p {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* === 空图表占位 === */
.empty-chart {
  height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  font-size: 14px;
}

/* === 统计卡片 === */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.stat-card {
  background: var(--color-bg-elevated);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--color-border);
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.stat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.stat-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
}

.stat-badge {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-badge.success {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.stat-badge.warning {
  background-color: var(--color-warning-light);
  color: var(--color-warning);
}

.stat-badge.info {
  background-color: #dbeafe;
  color: #3b82f6;
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
  margin-bottom: 12px;
}

.stat-value.text-warning {
  color: var(--color-warning);
}

.stat-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-trend {
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 20px;
}

.stat-trend.positive {
  background-color: var(--color-success-light);
  color: var(--color-success);
}

.stat-trend.negative {
  background-color: var(--color-danger-light);
  color: var(--color-danger);
}

.stat-trend.neutral {
  background-color: var(--color-border-light);
  color: var(--color-text-secondary);
}

.stat-compare {
  font-size: 13px;
  color: var(--color-text-tertiary);
}

/* === 图表区域 === */
.chart-section {
  background: var(--color-bg-elevated);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* === 告警图表区 === */
.alert-charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

/* === 快捷操作 === */
.quick-actions {
  margin-top: 8px;
}

.quick-actions .section-title {
  margin-bottom: 16px;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 24px;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-card:hover:not(:disabled) {
  border-color: var(--color-primary);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.action-card:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background-color: var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--color-text-secondary);
}

.action-icon.primary {
  background-color: var(--color-primary);
  color: white;
}

.action-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-primary);
}

@media (max-width: 1024px) {
  .alert-charts-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
```

- [ ] **Step 2: 验证 Dashboard 正常渲染**

启动前端 `npm run dev`，访问 Dashboard，确认 4 张图表正常显示，7 天/30 天切换正常。

- [ ] **Step 3: 验证防抖**

浏览器 Network 面板，快速点击 7 天 → 30 天 → 7 天，预期只触发 1 次（或最多 2 次）stats API 请求。

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Dashboard.vue
git commit -m "refactor: Dashboard 拆分图表组件 + 防抖 + loading/error/empty 状态"
```

---

### Task 10: 创建 notificationStore

**Files:**
- Create: `frontend/src/stores/notification.js`

- [ ] **Step 1: 创建 Pinia store**

```js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ElNotification } from 'element-plus'

const typeMap = { frequency: '频率异常', device: '设备异常' }
const severityMap = { low: '低', medium: '中', high: '高' }

export const useNotificationStore = defineStore('notification', () => {
  const unreadCount = ref(0)
  let eventSource = null

  function connect(token) {
    if (eventSource) return

    eventSource = new EventSource(`/api/notifications/stream?token=${token}`)

    eventSource.onmessage = (e) => {
      try {
        const alert = JSON.parse(e.data)
        unreadCount.value++
        ElNotification({
          title: '新告警',
          message: `${typeMap[alert.type] || alert.type} · ${severityMap[alert.severity] || alert.severity} · ${alert.username}`,
          type: alert.severity === 'high' ? 'error' : 'warning',
          duration: 5000,
        })
      } catch {
        // 解析失败跳过
      }
    }

    eventSource.onerror = () => {
      // 浏览器自动重连
    }
  }

  function clearUnread() {
    unreadCount.value = 0
  }

  function disconnect() {
    eventSource?.close()
    eventSource = null
    unreadCount.value = 0
  }

  return { unreadCount, connect, clearUnread, disconnect }
})
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/stores/notification.js
git commit -m "feat: 新增 notificationStore (SSE 连接 + 角标 + toast)"
```

---

### Task 11: MainLayout 集成 SSE + 侧边栏角标

**Files:**
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: 导航栏"告警列表"加 `el-badge`**

模板中 `menuItems` 的 `v-for` 循环之前（`<nav class="sidebar-nav">` 下方），用静态写法和角标：

```vue
<nav class="sidebar-nav">
  <router-link to="/" :class="['nav-item']">
    <el-icon :size="20"><Monitor /></el-icon>
    <span v-if="!isCollapse" class="nav-label">仪表盘</span>
  </router-link>
  <router-link to="/login-logs" :class="['nav-item']">
    <el-icon :size="20"><Document /></el-icon>
    <span v-if="!isCollapse" class="nav-label">登录日志</span>
  </router-link>
  <router-link to="/alerts" :class="['nav-item']">
    <el-icon :size="20"><WarningFilled /></el-icon>
    <span v-if="!isCollapse" class="nav-label">
      告警列表
      <el-badge
        :value="notificationStore.unreadCount"
        :hidden="notificationStore.unreadCount === 0"
        class="nav-badge"
      />
    </span>
  </router-link>
</nav>
```

- [ ] **Step 2: 移除 `menuItems` 数组和 `disabled` 属性**

删除 `<script setup>` 中的：

```js
const menuItems = [
  { path: '/', label: '仪表盘', icon: Monitor, disabled: false },
  { path: '/login-logs', label: '登录日志', icon: Document, disabled: false },
  { path: '/alerts', label: '告警列表', icon: WarningFilled, disabled: false },
]
```

- [ ] **Step 3: 引入 notificationStore + 建立/断开 SSE**

在 `<script setup>` 顶部加 import，并在 setup 体中加 `onMounted` / `onUnmounted`：

```js
import { useNotificationStore } from '../stores/notification'

const notificationStore = useNotificationStore()

// SSE 连接
onMounted(() => {
  const token = localStorage.getItem('token')
  if (token) {
    notificationStore.connect(token)
  }
})

onUnmounted(() => {
  notificationStore.disconnect()
})
```

同时确认 `onMounted` 和 `onUnmounted` 已从 Vue import（`import { computed, ref, onMounted, onUnmounted } from 'vue'`）。

- [ ] **Step 4: 添加角标样式**

在 `<style scoped>` 中 `.nav-label` 后面添加：

```css
.nav-badge {
  margin-left: 8px;
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/layouts/MainLayout.vue
git commit -m "feat: MainLayout 集成 SSE 连接 + 侧边栏角标"
```

---

### Task 12: Alerts.vue 加错误占位 + clearUnread

**Files:**
- Modify: `frontend/src/views/Alerts.vue`

- [ ] **Step 1: 模板加错误态**

把 `<div class="table-card" v-loading="loading">` 内的内容改为条件渲染：

```vue
<div class="table-card" v-loading="loading">
  <div v-if="error" class="error-placeholder">
    <p>数据加载失败，请稍后重试</p>
    <el-button type="primary" @click="fetchAlerts">重试</el-button>
  </div>

  <template v-else>
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
  </template>
</div>
```

- [ ] **Step 2: 脚本加 `error` ref + clearUnread**

```js
import { useNotificationStore } from '../stores/notification'

const notificationStore = useNotificationStore()
const error = ref(false)

const fetchAlerts = async () => {
  loading.value = true
  error.value = false
  try {
    const res = await getAlerts({
      skip: skip.value,
      limit: limit.value,
      ...currentFilters.value,
    })
    alerts.value = res.items
    total.value = res.total
  } catch (err) {
    console.error('Failed to fetch alerts:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAlerts()
  notificationStore.clearUnread()
})
```

- [ ] **Step 3: 样式加 `.error-placeholder`**

```css
.error-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 0;
}

.error-placeholder p {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/Alerts.vue
git commit -m "feat: Alerts 加错误占位 + clearUnread"
```

---

### Task 13: LoginLogs.vue 加错误占位

**Files:**
- Modify: `frontend/src/views/LoginLogs.vue`

- [ ] **Step 1: 模板加错误态**

```vue
<div class="table-card" v-loading="loading">
  <div v-if="error" class="error-placeholder">
    <p>数据加载失败，请稍后重试</p>
    <el-button type="primary" @click="fetchLogs">重试</el-button>
  </div>

  <template v-else>
    <LogTable v-if="logs.length > 0" :logs="logs" />
    <el-empty v-else description="暂无登录日志" />

    <LogPagination
      :total="total"
      :skip="skip"
      :limit="limit"
      @change="handlePageChange"
    />
  </template>
</div>
```

- [ ] **Step 2: 脚本加 `error` ref**

```js
const error = ref(false)

const fetchLogs = async () => {
  loading.value = true
  error.value = false
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
    error.value = true
  } finally {
    loading.value = false
  }
}
```

- [ ] **Step 3: 样式加 `.error-placeholder`**

```css
.error-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 60px 0;
}

.error-placeholder p {
  font-size: 15px;
  color: var(--color-text-secondary);
  margin: 0;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/LoginLogs.vue
git commit -m "feat: LoginLogs 加错误占位"
```

---

### Task 14: Vite 代理禁用 SSE 缓冲

**Files:**
- Modify: `frontend/vite.config.js`

- [ ] **Step 1: 修改 proxy 配置**

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api/notifications': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        ws: false,
        headers: { 'Connection': 'keep-alive' },
      },
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      },
    },
  },
})
```

> **要点：** `/api/notifications` 代理规则必须放在 `/api` 通用规则**前面**，否则 Vite 的长路径匹配会优先走 `/api` 规则。Vite proxy 按定义顺序匹配。

- [ ] **Step 2: Commit**

```bash
git add frontend/vite.config.js
git commit -m "feat: Vite 代理为 SSE 端点禁用缓冲"
```

---

### Task 15: 端到端验证

**前置条件：** `docker-compose up -d`（MySQL + Redis），后端 `uvicorn` 运行，Celery worker + beat 运行（验证 pub/sub 需要 Celery）。

- [ ] **Step 1: 验证 SSE 端点可连接**

```bash
# 先登录拿 token
curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
# 复制返回的 access_token

# 测试 SSE 端点连接（应保持连接并持续收到 heartbeat 注释行）
curl -N http://localhost:8001/api/notifications/stream?token=<TOKEN>
```
Expected: 持续输出 `: heartbeat` 注释行，连接不立即断开。

- [ ] **Step 2: 验证未授权被拒**

```bash
curl http://localhost:8001/api/notifications/stream
```
Expected: `{"detail":"..."}` 401 响应后立即断开。

- [ ] **Step 3: 验证 5xx 拦截器 toast**

停掉后端 `uvicorn`，访问 http://localhost:5173/login-logs，预期看到 "网络连接失败，请检查网络" toast + 页面显示错误占位 + 重试按钮。

- [ ] **Step 4: 验证 Dashboard loading/error/empty 态**

正常启动后端，访问 Dashboard：
- 加载时应看到 `v-loading` 遮罩
- 有数据时图表正常渲染
- 无数据时图表区域显示"暂无登录数据"/"暂无告警数据"等占位文字

- [ ] **Step 5: 验证防抖**

快速切换 7 天 → 30 天 → 7 天，Network 面板中 `/api/stats` 请求数 ≤ 2。

- [ ] **Step 6: 验证 Dashboard.vue 行数**

```bash
powershell -Command "(Get-Content frontend/src/views/Dashboard.vue).Count"
```
Expected: ≤ 250 行。

- [ ] **Step 7: Commit（如有微调）**

```bash
git add -A
git commit -m "chore: 端到端验证微调"
```

---

## 验证清单

| # | 验证项 | 方法 |
|---|--------|------|
| 1 | SSE 端点可连接并推送 heartbeat | `curl -N ...?token=...` |
| 2 | 无 token 返回 401 | `curl /api/notifications/stream` |
| 3 | Celery 检测发布 pub/sub | 写入触发异常的日志，观察 Redis pub/sub |
| 4 | Axios 5xx → toast | 停后端，访问任意页面操作 |
| 5 | Dashboard loading / error / empty 三态 | 访问 Dashboard，断开后端重新观测 |
| 6 | 告警/日志页面 error 占位 + 重试按钮 | 同上，访问 Alerts / LoginLogs |
| 7 | 4 张图表正常渲染 | Dashboard 正常数据 |
| 8 | 防抖 300ms | Network 面板快速切换 time range |
| 9 | Dashboard.vue ≤ 250 行 | `wc -l` |
| 10 | MainLayout 无 `menuItems` 遗留 | grep 确认无死代码 |
| 11 | Vite 代理 SSE 不缓冲 | 开发者工具 Network 查看 EventStream 响应头 `Transfer-Encoding: chunked` |
