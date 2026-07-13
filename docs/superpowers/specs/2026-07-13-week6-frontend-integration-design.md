# 第六周设计：前端页面联调 — 告警列表 + Dashboard 图表增强

> 日期：2026-07-13
> 范围：CLAUDE.md 第六周「前端页面联调：日志列表 + 告警列表 + ECharts 图表」
> 状态：设计已确认，待生成实现计划

## 背景与现状

**已完成**：
- 登录日志页 `LoginLogs.vue` 已联调 `GET /api/logs`，含筛选/表格/分页组件
- Dashboard 已联调 `GET /api/stats`，含 3 统计卡片 + 1 张登录趋势折线图
- 后端 `GET /api/alerts`（筛选+分页）、`GET /api/alerts/{id}`、`PUT /api/alerts/{id}` 已就绪

**缺口**：
- `Alerts.vue` 是占位页（仅显示"告警功能开发中"）
- 侧边栏「告警列表」`disabled: true`
- 无 `api/alerts.js`
- Dashboard 无告警维度图表
- 后端无告警统计接口

**本次不做**：
- 告警详情页/弹窗（行内操作即可）
- 关联日志展示与跳转
- 实时通知（第七周）
- 前端测试框架引入

## 整体架构

方案 A：复用现有模式。告警列表照搬 LoginLogs 的 Filter/Table/Pagination 三件套结构；Dashboard 图表 ECharts 配置内联，不抽离图表组件。

### 文件清单

| 文件 | 动作 | 说明 |
|------|------|------|
| `backend/app/api/stats.py` | 修改 | 新增 `GET /api/stats/alerts` 路由 |
| `frontend/src/api/alerts.js` | 新增 | `getAlerts(params)` / `updateAlertStatus(id, status)` |
| `frontend/src/api/stats.js` | 新增 | `getAlertStats(days)` |
| `frontend/src/views/Alerts.vue` | 重写 | 占位页 → 容器页（照抄 LoginLogs.vue 结构） |
| `frontend/src/views/Dashboard.vue` | 修改 | 新增告警区三张图表 + 调 `getAlertStats` |
| `frontend/src/components/alerts/AlertFilter.vue` | 新增 | 筛选：status / severity / username |
| `frontend/src/components/alerts/AlertTable.vue` | 新增 | 告警表格 + 行内状态变更下拉 |
| `frontend/src/components/alerts/AlertPagination.vue` | 新增 | 分页（复制 LogPagination 逻辑） |
| `frontend/src/components/common/StatusTag.vue` | 修改 | 扩展支持 alert status / severity / type 三种 tag |
| `frontend/src/layouts/MainLayout.vue` | 修改 | 侧边栏告警项 `disabled: true` → `false` |

**不改动**：`router/index.js`（`/alerts` 路由已存在）、`api/index.js`、`stores/auth.js`、后端 `api/alerts.py`。

### 数据流

```
告警列表页:
  Alerts.vue → api/alerts.js getAlerts() → GET /api/alerts → 后端已有
  Alerts.vue → api/alerts.js updateAlertStatus() → PUT /api/alerts/{id} → 后端已有

Dashboard 图表:
  Dashboard.vue → api/stats.js getAlertStats() → GET /api/stats/alerts → 新增后端路由
```

## 后端：GET /api/stats/alerts

在 `backend/app/api/stats.py` 内新增第二个路由，与现有 `GET /api/stats` 同文件。

**请求参数**：
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `days` | int | 7 | 统计窗口天数，前端传 7 或 30 |

鉴权：JWT（`get_current_active_user`），与现有 `/api/stats` 一致。

**响应结构**：
```json
{
  "alertTrend": [
    { "date": "07-07", "count": 3 }
  ],
  "typeDist": [
    { "name": "frequency", "value": 12 },
    { "name": "device", "value": 7 }
  ],
  "severityDist": [
    { "name": "low", "value": 4 },
    { "name": "medium", "value": 10 },
    { "name": "high", "value": 5 }
  ]
}
```

**查询逻辑**：
1. `alertTrend`：逐日循环 `days` 天，统计每天 `created_at` 落在该日范围内的告警数。与现有 `loginTrend` 对称，查 `Alert` 模型，时间字段 `created_at`。
2. `typeDist`：`db.query(Alert.alert_type, func.count()).filter(Alert.created_at >= window_start).group_by(Alert.alert_type).all()`，窗口起点 `now - timedelta(days=days)`。
3. `severityDist`：同上，`group_by(Alert.severity)`。

**不做**：不加 Pydantic response_model（与现有 `/api/stats` 风格一致）、不加缓存、不分页。

## 前端 API 层

### `frontend/src/api/alerts.js`（新增）

```js
import api from './index'

export function getAlerts(params) {
  return api.get('/api/alerts', { params })
}

export function updateAlertStatus(alertId, status) {
  return api.put(`/api/alerts/${alertId}`, { status })
}
```

- `getAlerts` 接收 `{ status, severity, username, skip, limit }`
- 响应已被 `api/index.js` 拦截器 `response.data` 解包

### `frontend/src/api/stats.js`（新增）

```js
import api from './index'

export function getAlertStats(days = 7) {
  return api.get('/api/stats/alerts', { params: { days } })
}
```

### Dashboard.vue 调用方式

- 登录维度数据继续用 `api.get('/api/stats')`（不动，避免回归）
- 告警维度数据用 `import { getAlertStats } from '../api/stats'`
- 两接口 `Promise.all` 并发

## 告警列表页

### Alerts.vue 容器页

照抄 LoginLogs.vue 结构：

```vue
<template>
  <div class="alerts-page">
    <AlertFilter @search="handleSearch" @reset="handleReset" />
    <div class="table-card" v-loading="loading">
      <AlertTable v-if="alerts.length > 0" :alerts="alerts" @status-change="handleStatusChange" />
      <el-empty v-else description="暂无告警" />
      <AlertPagination
        :total="total" :skip="skip" :limit="limit"
        @change="handlePageChange"
      />
    </div>
  </div>
</template>
```

状态管理：`alerts / total / skip / limit / loading / currentFilters` 六个 ref。

`fetchAlerts()` 调 `getAlerts({ skip, limit, ...currentFilters })`，`onMounted(fetchAlerts)`。

`handleStatusChange(alertId, newStatus)`：调 `updateAlertStatus` 成功后重新 `fetchAlerts()` 刷新当前页（不局部更新，保持简单）。

### AlertFilter.vue

三个筛选项：

| 字段 | 组件 | 选项 |
|------|------|------|
| status | el-select | pending（待处理）/ acknowledged（已确认）/ resolved（已处理） |
| severity | el-select | low（低）/ medium（中）/ high（高） |
| username | el-input | 文本模糊匹配 |

布局与 LogFilter 一致。emit `search(params)` / `reset()`，params 只包含非空字段。

### AlertTable.vue

表格列：

| 列 | 字段 | 宽度 | 渲染 |
|----|------|------|------|
| ID | id | 60 | 纯文本 |
| 用户名 | username | 100 | 纯文本 |
| 告警类型 | alert_type | 100 | StatusTag type="alert_type" |
| 级别 | severity | 80 | StatusTag type="alert_severity" |
| 状态 | status | 100 | StatusTag type="alert_status" |
| 告警内容 | alert_message | 弹性 | tooltip 截断（同 LogTable user_agent 列） |
| 创建时间 | created_at | 150 | formatDateTime |
| 操作 | — | 80 | el-dropdown 行内状态变更 |

**行内状态变更下拉**（操作列）：
- el-dropdown trigger="click"，三个 command：`pending` / `acknowledged` / `resolved`
- 当前状态对应项 `disabled`，防重复设置
- 三个选项全列（无约束转换）
- emit `status-change(alertId, cmd)` 给父组件

### AlertPagination.vue

从 LogPagination.vue 复制改名，逻辑完全相同（`total / skip / limit` props，`change` emit）。不抽公共组件。

### StatusTag.vue 扩展

新增 `type` prop，默认 `'login'`：

| type | 值 | label | 样式 |
|------|-----|-------|------|
| `login`（现有） | success/failure | 成功/失败 | success-light/danger-light |
| `alert_status` | pending/acknowledged/resolved | 待处理/已确认/已处理 | warning-light/info-light/success-light |
| `alert_severity` | low/medium/high | 低/中/高 | info-light/warning-light/danger-light |
| `alert_type` | frequency/device | 频率异常/设备异常 | 中性灰底（`--color-border-light` + `--color-text-secondary`） |

### MainLayout.vue

侧边栏 menuItems 告警项 `disabled: true` → `false`。

## Dashboard 图表增强

### 布局

```
Dashboard
├── 统计卡片（3个，不动）
├── 登录区：登录趋势折线图（现有，不动）
├── 告警分析区（新增）
│   ├── 告警趋势折线图（占整宽）
│   └── 下方两列
│       ├── 告警类型分布环形图
│       └── 严重级别分布柱状图
└── 快捷操作（不动）
```

### 数据获取改造

`refreshData()` 改为 `Promise.all` 并发调 `/api/stats` + `getAlertStats(days)`。

### 三张图表 ECharts 配置

**1. 告警趋势折线图**：与登录趋势对称，配色 `#F59E0B`（warning 色），line + areaStyle 渐变。容器高 320px，占整宽。

**2. 告警类型分布环形图**：pie 类型，`radius: ['45%', '70%']`，颜色 `['#111827', '#F59E0B']`，legend 显示「频率异常/设备异常」。容器高 280px，与级别柱状图并排。

**3. 严重级别分布柱状图**：bar 类型，按级别着色 `low:#3B82F6 / medium:#F59E0B / high:#EF4444`，`barWidth: '40%'`，`borderRadius: [6,6,0,0]`。容器高 280px，与类型环形图并排。

### 图表实例管理

四个 ECharts 实例。`refreshData` 中先全部 `dispose()` 旧实例再重建（沿用现有登录趋势重建模式）。`onUnmounted` 中全部 `dispose()`。

### 空数据处理

- 折线图：空轴
- 环形图：空白圆环 + 空 legend
- 柱状图：三级别标签 + 0 柱

不额外做"无数据"提示，与现有登录趋势图行为一致。

## 测试与验证

### 后端测试

新增 `backend/tests/test_alert_stats.py`，用 `client` fixture（走真实 app，需 Docker MySQL）：

1. 未登录访问返回 401
2. 登录后返回正确结构（含 `alertTrend` / `typeDist` / `severityDist` 三个 key）
3. `alertTrend` 长度等于 `days` 参数
4. `days=30` 时 `alertTrend` 长度为 30

不测具体数值（依赖数据库内容，不稳定）。

### 前端手动验证

**告警列表页**：
- [ ] 侧边栏「告警列表」可点击，不再灰显
- [ ] 空数据时显示 `el-empty`「暂无告警」
- [ ] 有数据时表格渲染，列与字段对应
- [ ] status / severity / username 筛选 → 表格刷新
- [ ] 分页切换 → 表格刷新
- [ ] 行内下拉切换状态 → PUT 成功后列表刷新
- [ ] 下拉中当前状态项 disabled

**Dashboard**：
- [ ] 切换近7天/近30天，四张图全部刷新
- [ ] 告警趋势折线图 x 轴日期数量与 days 一致
- [ ] 类型分布环形图 legend 显示「频率异常/设备异常」
- [ ] 级别分布柱状图 x 轴显示「低/中/高」
- [ ] 空数据时图表不报错
- [ ] 页面切换/刷新无 ECharts 实例泄漏

### 启动依赖

Docker Compose 在跑（MySQL + Redis:8880），`alembic upgrade head` + `python scripts/seed.py` 已执行。后端 `:8001`、前端 `:5173`。

### 不做的测试

- 前端单元测试（项目无前端测试框架）
- AlertTable/AlertFilter 组件测试
- ECharts 快照测试

## 遵循的约定

- UI 风格遵循 `docs/UI.md`（配色 #111827 主色、间距 32/24/16、卡片圆角 12px）
- 后端新路由挂 `prefix=settings.API_V1_PREFIX`（`/api`）
- 后端响应不加 Pydantic response_model，与现有 `/api/stats` 一致
- 前端组件 CSS 用 `var(--color-*)` token，不硬编码色值（ECharts 配置内除外，同现有 Dashboard）
- 不引入新依赖（ECharts / Element Plus 已在 package.json）
