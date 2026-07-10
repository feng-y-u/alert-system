# 登录日志前端重构设计

## 概述

基于 `docs/UI.md` 设计规范，对登录日志页面（`/login-logs`）进行 UI 重构。后端 API 已完备，本次仅涉及前端表现层改造。

## 范围

| 文件 | 改动类型 |
|------|----------|
| `frontend/src/views/LoginLogs.vue` | 重构 — 页面容器，统一加载/空状态 |
| `frontend/src/components/logs/LogFilter.vue` | 重构 — 筛选器卡片 |
| `frontend/src/components/logs/LogTable.vue` | 重构 — 表格卡片，新增列 |
| `frontend/src/components/logs/LogPagination.vue` | 微调 — 放入表格卡片内部 |
| `frontend/src/components/common/StatusTag.vue` | 微调 — 改用 badge 样式 |

## 设计细节

### 1. 整体布局

```
┌────────────────────────────────────────────────────────┐
│  [筛选器卡片]  card, border-radius:12px, padding:24px   │
│  ┌────────────────────────────────────────────────────┐  │
│  │ 用户名 │ IP地址 │ 状态 │ 日期范围 │ 查询 │ 重置 │  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  [表格卡片]  card + shadow, padding:24px                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │  ID │ 用户名 │ 状态 │ 登录时间 │ IP │ 用户代理    │  │  │
│  ├────────────────────────────────────────────────────┤  │  │
│  │  ...数据行...                                      │  │  │
│  ├────────────────────────────────────────────────────┤  │  │
│  │  ────────── 共 N 条  ◀ 1 2 3 4 ▶ ──────────────  │  │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 2. 列定义

| 列 | 宽度 | key | 渲染 |
|----|------|-----|------|
| ID | 80px | `id` | 纯文本 |
| 用户名 | 120px | `username` | 纯文本 |
| 状态 | 80px | `login_status` | `<StatusTag>` badge 组件 |
| 登录时间 | 170px | `login_time` | `YYYY-MM-DD HH:mm` 格式 |
| IP 地址 | 140px | `ip_address` | 纯文本 |
| 用户代理 | min-width 200px, flex:1 | `user_agent` | `el-tooltip effect="dark"` 包裹截断文本 |

### 3. 10 项规范细节

| # | 项 | 实现方式 |
|---|----|----------|
| 1 | **StatusTag badge 色** | 成功：`bg #D1FAE5` + `color #10B981`；失败：`bg #FEE2E2` + `color #EF4444`，`border-radius: 20px` |
| 2 | **表头背景** | `#F9FAFB`（`var(--color-bg)`），与白色卡片形成对比 |
| 3 | **分隔线** | th 底部 `#E5E7EB`，td 底部 `#F3F4F6` |
| 4 | **筛选器高度对齐** | 所有输入框、下拉框、按钮统一 `height: 40px` |
| 5 | **日期选择器圆角** | 覆盖为 `8px`，与按钮一致 |
| 6 | **分页位置** | 放在表格卡片内部，底部 `padding-top: 16px` |
| 7 | **user_agent tooltip** | `el-tooltip effect="dark"` + 文本截断 `text-overflow: ellipsis` |
| 8 | **表格卡片阴影** | `box-shadow: 0 1px 3px rgba(0,0,0,0.05)` |
| 9 | **加载/空状态** | `v-loading` 加载中，`el-empty` 空数据（描述色 `#9CA3AF`） |
| 10 | **响应式** | 表格启用横向滚动，筛选器 `flex-wrap: wrap` 自动换行 |

### 4. 数据流

```
LoginLogs.vue (容器)
  ├─ fetchLogs() → api/logs.js → GET /api/logs → 响应
  ├─ 传给 LogFilter: @search, @reset
  ├─ 传给 LogTable: :logs
  └─ 传给 LogPagination: :total, :skip, :limit, @change

LogFilter.vue (筛选器)
  ├─ 本地 reactive 状态
  ├─ 查询 → emit('search', params)  → 父组件重置 skip=0 并重新取数
  └─ 重置 → emit('reset') → 父组件清空 filters 并重新取数

LogTable.vue (展示)
  ├─ props: logs
  └─ 纯展示，无内部状态

LogPagination.vue (分页)
  ├─ props: total, skip, limit
  ├─ computed: 双向绑定 currentPage / pageSize
  └─ emit('change', skip, limit) → 父组件更新 skip/limit 并重新取数
```

### 5. 无新增后端改动

后端 `GET /api/logs` 已返回全量字段（`id`, `username`, `login_time`, `ip_address`, `user_agent`, `login_status`），前端直接消费即可。

## 非目标

- 不修改后端 API、模型、schema
- 不涉及登录日志的接收功能（`POST /api/logs`）
- 不添加导出、批量操作等新功能
- 不改动布局 `MainLayout.vue` 和全局样式 `App.vue`