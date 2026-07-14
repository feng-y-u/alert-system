# 第 7 周功能完善设计：实时通知 + 优化 + 错误处理

**日期：** 2026-07-14  
**主题：** SSE 实时告警通知 / 前端错误处理加固 / Dashboard 图表组件化优化

---

## 1. 目标

第 7 周计划"功能完善：实时通知 + 优化 + 错误处理"的落地方案，分三块独立交付：

- **实时通知**——SSE 轻量推送，新告警秒级到达前端
- **错误处理**——全局拦截器 + 各页面 loading/error/empty 三态
- **优化**——Dashboard.vue 拆分图表子组件 + time range 防抖

三块工作完全独立，可并行推进。

---

## 2. 整体架构与数据流

```
[Celery 检测任务]                         [前端浏览器]
  detect_anomaly_for_log                   MainLayout
  run_anomaly_detection                        │
        │                                      ├─ EventSource("/api/notifications/stream")
        ▼                                      │     (只读单向连接，浏览器自动重连)
  redis.publish("alerts", payload)  ──────►  [FastAPI SSE 端点]
                                                ├─ pubsub.subscribe("alerts")
                                                │
                                                ├─ yield 推送 → 前端
                                                │
                                                ▼
                                           前端 Pinia notificationStore
                                                ├─ unreadCount++  → 侧边栏角标
                                                └─ ElNotification 弹出

[用户点进告警页] → unreadCount = 0 → 角标消失 → 告警列表自动 fetchAlerts()
```

### 关键设计点

- **数据流单向**——后端产生告警事件 → Redis pub/sub → SSE 端点 → 浏览器。前端无回写需求。
- **Redis 双用**——既是 Celery broker 又是 pub/sub 通道，无新依赖。
- **SSE 端点用 FastAPI `StreamingResponse`**——`media_type="text/event-stream"`，generator 循环 `pubsub.get_message()` 并 `yield` 格式化 SSE 事件块。
- **前端用原生 `EventSource`**——浏览器内置，自动断线重连，无新库。
- **连接生命周期**——MainLayout `onMounted` 建 EventSource，`onUnmounted`/登出调 `.close()`。
- **鉴权**——`EventSource` 无法设置 header，SSE 端点用 query param `?token=<jwt>` 鉴权。

---

## 3. 后端 SSE 端点与 Redis pub/sub

### Redis pub/sub 集成

Celery 检测任务在生成告警后，新增一步 Redis 发布（与现有 `send_alert_email.delay()` 并列）：

```python
# app/tasks/detection.py（实时检测 + 定时检测，各加一处）
import redis, json
from app.core.config import settings

def _publish_alert_event(alert: Alert):
    r = redis.Redis.from_url(settings.REDIS_URL)
    r.publish("alerts", json.dumps({
        "alert_id": alert.id,
        "type": alert.alert_type,
        "severity": alert.severity,
        "username": alert.username,
    }))
```

- 复用现有 `settings.REDIS_URL`（`redis://localhost:8880/0`）
- 每次发布即断开连接（短连接）
- 频率低（仅新告警产生时），无性能压力

### SSE 端点

新增 `app/api/notifications.py`：

```python
@router.get("/notifications/stream")
async def stream_notifications(token: str, db: Session = Depends(get_db)):
    user = verify_token(token, db)  # query param 鉴权，无效则 401
    r = redis.Redis.from_url(settings.REDIS_URL)
    pubsub = r.pubsub()
    pubsub.subscribe("alerts")

    async def event_generator():
        try:
            while True:
                message = pubsub.get_message(timeout=1.0)
                if message and message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                else:
                    yield f": heartbeat\n\n"  # 保活注释行
        finally:
            pubsub.unsubscribe("alerts")
            pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

### 关键点

- **鉴权**——`?token=<jwt>` query param。`verify_token` 解析校验，无效则 401。SSE 标准做法。
- **注册路由**——`app/main.py` 中 `app.include_router(notifications.router, prefix=settings.API_V1_PREFIX)`（AGENTS.md 强制步骤）
- **Heartbeat**——每秒发送 `: heartbeat\n\n` 注释行，防止代理/浏览器超时断连。
- **同步 Redis + async generator**——本周不引入 `aioredis`，用同步 `redis.Redis` + `get_message(timeout=1.0)` 轮询，配合 async `yield`。单用户量级足够。
- **单频道**——第 7 周只需"新告警"一个事件，`pubsub.subscribe("alerts")` 即可，不做多频道。
- **推送精简字段**——`{alert_id, type, severity, username}` 四字段，Toast 显示"新告警：频率异常 · 高 · zhang_san"，角标仅累计计数。用户点进告警页时自动 fetchAlerts 看完整列表。

### 新增 / 修改文件

| 文件 | 说明 |
|------|------|
| `backend/app/api/notifications.py` | 新增：SSE 端点 |
| `backend/app/tasks/detection.py` | 修改：两处告警生成点新增 `_publish_alert_event()` |
| `backend/app/main.py` | 修改：注册 notifications router |

---

## 4. 前端实时通知与角标

### notificationStore（Pinia）

新增 `frontend/src/stores/notification.js`：

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
    eventSource = new EventSource(`/api/notifications/stream?token=${token}`)
    eventSource.onmessage = (e) => {
      const alert = JSON.parse(e.data)
      unreadCount.value++
      ElNotification({
        title: '新告警',
        message: `${typeMap[alert.type]} · ${severityMap[alert.severity]} · ${alert.username}`,
        type: alert.severity === 'high' ? 'error' : 'warning',
      })
    }
    eventSource.onerror = () => { /* 浏览器自动重连，无需手动 */ }
  }

  function clearUnread() { unreadCount.value = 0 }
  function disconnect() { eventSource?.close(); eventSource = null; unreadCount.value = 0 }

  return { unreadCount, connect, clearUnread, disconnect }
})
```

### MainLayout 集成

```js
import { useNotificationStore } from '@/stores/notification'

const notificationStore = useNotificationStore()
const token = localStorage.getItem('token')
onMounted(() => notificationStore.connect(token))
onUnmounted(() => notificationStore.disconnect())
```

### 侧边栏角标

```html
<el-badge :value="notificationStore.unreadCount" :hidden="notificationStore.unreadCount === 0">
  告警管理
</el-badge>
```

### 告警页清零

`Alerts.vue` 的 `onMounted` 中调 `notificationStore.clearUnread()`——用户点进告警页即归零，刷新或重新登录后角标自然重置（内存计数，无持久化）。

### Vite 代理

`vite.config.js` 为 SSE 端点禁用代理缓冲：

```js
'/api/notifications': {
  target: 'http://localhost:8001',
  changeOrigin: true,
  ws: false,
  headers: { 'Connection': 'keep-alive' },
}
```

### 新增 / 修改文件

| 文件 | 说明 |
|------|------|
| `frontend/src/stores/notification.js` | 新增：SSE 连接 + 未读计数 + toast |
| `frontend/src/layouts/MainLayout.vue` | 修改：建立/断开 SSE，侧边栏加角标 |
| `frontend/src/views/Alerts.vue` | 修改：`onMounted` 调 `clearUnread()` |
| `frontend/vite.config.js` | 修改：notifications 代理禁用缓冲 |

---

## 5. 错误处理（L1 拦截器 + L2 页面三态）

### L1：Axios 拦截器扩展

修改 `frontend/src/api/index.js`，在现有 401 处理基础上增加全局 toast：

```js
import { ElMessage } from 'element-plus'

service.interceptors.response.use(
  response => response.data,
  error => {
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
    // 4xx (非 401/403/429) 不弹 toast，由调用方按业务逻辑处理

    return Promise.reject(error)
  }
)
```

- **原则**：拦截器弹"非业务可预期"错误（5xx/网络/权限/限流）；业务级 4xx（如 400 校验）由调用方 catch 处理。
- **ElNotification vs ElMessage 分工**——ElNotification 用于告警推送（异步、常驻），ElMessage 用于操作错误反馈（同步、短暂），职责拆开。

### L2：各页面补 loading/error/empty 三态

| 页面 | 当前状态 | 补什么 |
|------|---------|--------|
| **Dashboard.vue** | 无 loading、无错误态、无空态 | `loading` ref + `v-loading` 包裹图表区；`error` ref，失败时显示"数据加载失败，请稍后重试"占位块；无数据时图表显示"暂无数据" |
| **Alerts.vue** | 有 loading + 空态，但 catch 静默 | catch 中设 `error` ref，失败时显示错误占位而非仅 `el-empty` |
| **LoginLogs.vue** | 同 Alerts | 同上 |
| **Login.vue** | 已完善 | 不动 |

**错误态交互**——在页面数据位显示错误占位（含"重试"文字按钮），不只弹 toast 后消失，便于用户定位是哪部分出错。

**AlertTable 行内状态更新**——现有 `handleStatusChange` 已用 `ElMessage.success/error`，保留不动（属操作级反馈，非数据加载错误）。

### 新增 / 修改文件

| 文件 | 说明 |
|------|------|
| `frontend/src/api/index.js` | 修改：拦截器扩展 5xx/403/429/网络错误全局 toast |
| `frontend/src/views/Dashboard.vue` | 修改：新增 loading/error/空态 |
| `frontend/src/views/Alerts.vue` | 修改：新增 error 占位态 |
| `frontend/src/views/LoginLogs.vue` | 修改：新增 error 占位态 |

### L3 留给第 8 周扩展（本周不做）

以下内容作为"留给第 8 周测试与部署时扩展"的提醒，**本周不实现**：

- **离线检测**——`navigator.onLine` + `online/offline` 事件 → 全局 banner 提示网络断开
- **请求超时友好反馈**——axios timeout 已设 10s，超时时给出"请求超时"明确提示，而非通用"网络连接失败"
- **错误占位重试节流**——"重试"按钮加 cooldown（如 5s），避免用户连击产生请求风暴
- **SSE 断线期间的告警补漏**——断线恢复后，因 pub/sub 不缓存历史消息，错过的告警无法主动推送。需考虑新增"获取断线期间未读告警"的增量查询接口，或在 SSE 重连后前端主动 fetch 一次最新告警列表对比本地最大 alert_id

---

## 6. Dashboard 优化（拆分图表组件 + 防抖）

### 拆分方案

把 Dashboard 内联的 4 个图表抽成独立组件，每个接收 `data` prop，内部自管 ECharts 生命周期：

| 新组件 | 接收 prop | 图表类型 |
|--------|-----------|---------|
| `components/charts/LoginTrendChart.vue` | `data: [{date, count}]` | 折线图 |
| `components/charts/AlertTrendChart.vue` | `data: [{date, count}]` | 折线图（琥珀色） |
| `components/charts/TypeDistChart.vue` | `data: [{name, value}]` | 环形图 |
| `components/charts/SeverityDistChart.vue` | `data: [{name, value}]` | 柱状图 |

### chart 组件统一结构

```vue
<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({ data: { type: Array, default: () => [] } })
const chartRef = ref(null)
let chart = null

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
```

- ECharts option 配置从 Dashboard 原内联代码迁移到各组件的 `buildOption()` 函数
- `watch` 深度比较 prop 引用即可——Dashboard 重拉数据时新数组引用自然触发 render
- 视觉效果与现有保持一致（动画、配色、字号），仅做职责拆分

### Dashboard 主体简化

```vue
<template>
  <div v-loading="loading">
    <div class="stats-grid">...</div>
    <LoginTrendChart :data="trend" />
    <AlertTrendChart :data="alertTrend" />
    <div class="alert-charts-grid">
      <TypeDistChart :data="typeDist" />
      <SeverityDistChart :data="severityDist" />
    </div>
  </div>
</template>
```

预计 Dashboard 主体从 601 行降至约 200 行，图表配置散在 4 个独立组件中（各约 100-130 行）。

### Time range 防抖

```js
import { debounce } from 'lodash-es'
const debouncedRefresh = debounce(refreshData, 300)
watch(timeRange, debouncedRefresh)
```

- `lodash-es` 已在依赖列表（ECharts 依赖链带入）
- 300ms 挡掉用户快速切换 time range 时的多次请求

### 新增 / 修改文件

| 文件 | 说明 |
|------|------|
| `frontend/src/components/charts/LoginTrendChart.vue` | 新增：登录趋势折线图组件 |
| `frontend/src/components/charts/AlertTrendChart.vue` | 新增：告警趋势折线图组件 |
| `frontend/src/components/charts/TypeDistChart.vue` | 新增：类型分布环形图组件 |
| `frontend/src/components/charts/SeverityDistChart.vue` | 新增：级别分布柱状图组件 |
| `frontend/src/views/Dashboard.vue` | 修改：内联图表配置移出、改为子组件引用、加防抖 |

---

## 7. 文件变更汇总

### 后端（3 个文件）

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/api/notifications.py` | 新增 | SSE 端点 |
| `backend/app/tasks/detection.py` | 修改 | 两处告警生成点新增 `_publish_alert_event()` |
| `backend/app/main.py` | 修改 | 注册 notifications router |

### 前端（11 个文件，7 修改 + 4 新增）

| 文件 | 类型 | 说明 |
|------|------|------|
| `frontend/src/stores/notification.js` | 新增 | Pinia SSE 连接 + 未读计数 + toast |
| `frontend/src/api/index.js` | 修改 | 拦截器扩展全局 toast |
| `frontend/src/layouts/MainLayout.vue` | 修改 | 建立 SSE、侧边栏角标 |
| `frontend/src/views/Alerts.vue` | 修改 | error 占位态 + clearUnread |
| `frontend/src/views/LoginLogs.vue` | 修改 | error 占位态 |
| `frontend/src/views/Dashboard.vue` | 修改 | loading/error/空态 + 引用子组件 + 防抖 |
| `frontend/src/components/charts/LoginTrendChart.vue` | 新增 | 登录趋势折线图 |
| `frontend/src/components/charts/AlertTrendChart.vue` | 新增 | 告警趋势折线图 |
| `frontend/src/components/charts/TypeDistChart.vue` | 新增 | 类型分布环形图 |
| `frontend/src/components/charts/SeverityDistChart.vue` | 新增 | 级别分布柱状图 |
| `frontend/vite.config.js` | 修改 | notifications 代理禁用缓冲 |

---

## 8. 验收标准

| 编号 | 标准 | 验证方式 |
|------|------|---------|
| V1 | Celery 检测生成新告警后，已连接的浏览器在 2s 内弹出 toast 通知 | 触发 `POST /api/logs` 写入触发频率异常的日志，观察浏览器 |
| V2 | 侧边栏"告警管理"菜单显示未读角标，点进告警页后角标消失 | 观察 MainLayout 侧边栏 |
| V3 | 刷新页面或重新登录后角标重置为 0 | 浏览器刷新 |
| V4 | SSE 端点未带 token 或 token 无效时返回 401 | curl `http://localhost:8001/api/notifications/stream` 无 token |
| V5 | Dashboard 加载中显示 loading，加载失败显示错误占位 | 断开后端 + 访问 Dashboard |
| V6 | 告警/日志页加载失败显示错误占位（而非空白） | 断开后端 + 访问告警/日志页 |
| V7 | Axios 拦截器在 5xx / 网络失败时弹全局 toast | 停后端 + 任意页面操作 |
| V8 | Dashboard.vue 主体行数 ≤ 250 行，图表逻辑在 4 个子组件中 | `wc -l` |
| V9 | Time range 快速切换 3 次只触发 1 次 API 请求 | 浏览器 Network 面板 |

---

## 9. 不做范围（YAGNI）

- **WebSocket 双向通信**——DESIGN.md 列为"后续扩展"，本周无主动推送需求
- **通知中心 / 已读持久化**——后端不新增字段，角标纯前端内存
- **多频道 SSE**——本周只需"新告警"，不做 logs/severity 等多频道
- **AIoredis**——同步 `redis.Redis` + 轮询够用，不引入 async Redis 库
- **L3 错误处理**——离线检测/超时反馈/重试节流/SSE 补漏放第 8 周（见 §5 L3 提醒）
- **移动端适配**——DESIGN.md 后续扩展，不在本周

---

## 10. 参考资料

- [DESIGN.md](../../DESIGN.md)——第 7 周计划
- [AGENTS.md](../../AGENTS.md)——Redis 端口、路由注册强制步骤、环境变量
- [第六周周记](../第六周周记.md)——Dashboard/告警页当前实现状态