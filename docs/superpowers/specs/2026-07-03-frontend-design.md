# 前端页面设计方案

**校园账号异常登录监测与告警平台**

> 文档版本：v1.0
> 创建日期：2026-07-03
> 设计方向：B — 极简「白 + 浅灰」

---

## 1. 设计总则

### 1.1 设计理念

- **简约（Minimal）** — 去除冗余装饰，用留白和字重划分层级
- **大气（Elegant）** — 深蓝侧栏构建稳重感，白色内容区保证清晰度
- **高效（Efficient）** — 数据一目了然，操作路径最短

### 1.2 角色定位

本系统是**监控/运维类平台**，用户为**管理员**，核心任务是查看登录日志、发现异常、处理告警。设计需服务于"快速识别异常 → 快速处理"的工作流。

---

## 2. 设计 Token

### 2.1 色彩体系

| 用途 | 色值 | 场景 |
|------|------|------|
| 侧栏/顶栏背景 | `#1a1a2e` | 主导航区域 |
| 卡片/内容背景 | `#ffffff` | 所有卡片、表单、弹窗 |
| 页面背景 | `#f8f9fa` | 内容区底衬 |
| 品牌色 / Primary | `#2563eb` | 主要按钮、链接、活跃态 |
| Primary Hover | `#3b82f6` | 按钮悬停、辅助蓝色 |
| 成功 / 正常 | `#10b981` | 登录成功、已处理 |
| 警告 / 可疑 | `#f59e0b` | 异常警告、可疑状态 |
| 危险 / 告警 | `#ef4444` | 高风险告警、错误提示 |
| 边框 / Divider | `#e5e7eb` | 卡片边框、分割线 |
| 表格行悬停 | `#f3f4f6` | 表格 hover 高亮 |
| 正文文字 | `#111827` | 标题、表格正文、按钮文字 |
| 次要文字 | `#6b7280` | 说明文字、数据来源标注 |
| 占位文字 | `#9ca3af` | 输入框 placeholder |

### 2.2 字体体系

| 层级 | 字号 | 字重 | 色值 | 用途 |
|------|------|------|------|------|
| H1 | 24px | 700 | `#111827` | 页面大标题（极少使用） |
| H2 | 20px | 600 | `#111827` | 页面标题 |
| H3 / 卡片头部 | 16px | 500 | `#111827` | 卡片标题、区域标题 |
| **正文 / 按钮** | **14px** | **400** | **`#111827`** | **所有正文、按钮文字、表格内容** |
| 辅助文字 | 13px | 400 | `#6b7280` | 说明、标签、数据源标注 |
| 小标签 | 12px | 400 | `#9ca3af` | 时间轴、次要标签 |

**字体栈：**

```css
font-family: 'Inter', 'Noto Sans SC', -apple-system, 'Helvetica Neue',
             'PingFang SC', 'Microsoft YaHei', sans-serif;
```

- 英文数字使用 Inter（清晰现代），中文使用 Noto Sans SC
- 按钮文字与正文统一：**14px · 400 weight**（不加粗、不缩小）

### 2.3 间距体系

遵循 4px 基准递进：

```
4px · 8px · 12px · 16px · 20px · 24px · 32px · 48px
```

- 卡片内边距：20px
- 卡片间距：16px（grid gap）
- 段落间距：16px
- 元素内间距（按钮/输入框）：0 12px（水平），0 20px（含文本按钮）

### 2.4 圆角体系

| 层级 | 值 | 用途 |
|------|----|------|
| 轻微 | 6px | 图标容器 |
| 中等 | 8px | 按钮、输入框、导航项 |
| 卡片 | 10px | 统计卡片、图表卡片 |
| 标签 | 999px | 状态标签（胶囊形） |

### 2.5 阴影

默认无阴影，仅 hover 态使用轻微阴影：

```css
box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
```

---

## 3. 页面布局

### 3.1 MainLayout — 整体布局

```
┌─────────────────────────────────────┐
│  ┌──────────┬──────────────────────┐ │
│  │          │  Header (56px)       │ │
│  │ Sidebar  │  #ffffff 面包屑 │ 用户  │ │
│  │ 220px    ├──────────────────────┤ │
│  │ #1a1a2e  │                      │ │
│  │          │  Content             │ │
│  │          │  #f8f9fa             │ │
│  │          │                      │ │
│  └──────────┴──────────────────────┘ │
└─────────────────────────────────────┘
```

**侧边栏 (220px)：**
- 深蓝背景 `#1a1a2e`，活跃项蓝色高亮 `rgba(37,99,235,0.15)` + 蓝色文字
- 非活跃项文字 `rgba(255,255,255,0.7)`，图标 `rgba(255,255,255,0.5)`
- 底部系统设置与导航分隔
- 告警项右侧显示红色角标数字
- 可折叠至 64px（仅图标），动画过渡 0.3s

**顶栏 (56px)：**
- 白色背景 + 底部极细边框 `#e5e7eb`
- 左侧：折叠按钮 + 面包屑
- 右侧：用户名 + 圆形头像占位

### 3.2 登录页

```
┌─────────────────────────────────────┐
│                                     │
│          ┌───────────────┐          │
│          │   品牌 Logo    │          │
│          │  管理员登录     │          │
│          │  平台名称      │          │
│          │               │          │
│          │  用户名输入框   │          │
│          │  密码输入框     │          │
│          │  [    登录    ]│          │
│          │  版权信息      │          │
│          └───────────────┘          │
│                                     │
└─────────────────────────────────────┘
```

- 居中卡片，宽度 400px，白底+细边框+微阴影
- 输入框带图标前缀（👤用户名 / 🔒密码）
- 聚焦时边框变 `#2563eb`
- 登录按钮与正文统一 14px/400w

**状态覆盖：**

| 状态 | 表现 |
|------|------|
| 空字段 | 红色边框 `#ef4444` + 红色错误文字 |
| 加载中 | 按钮置灰 + 旋转动画，输入框 disabled |
| 错误提示 | 顶部红色提示条 bg:`#fef2f2` color:`#991b1b` |

### 3.3 Dashboard 页

**统计卡片（4列）：**

| 卡片 | 数据来源 | 关键字段 |
|------|----------|----------|
| 今日登录 | LoginLog | `login_time` 今日 count |
| 失败次数 | LoginLog | `login_status=failure` count |
| 待处理告警 | Alert | `status=pending` count |
| 告警处理率 | Alert | `resolved / total` |

每张卡片：白底+细边框+圆角，数字 28px/700w，标签 13px/400w/`#6b7280`。

**图表区（2:1 比例）：**
- 左 2/3：折线图（ECharts），展示登录趋势，带虚线阈值线
- 右 1/3：告警类型分布（堆叠进度条），按 `alert_type` 分组

**最近告警表格：**
- 字段：告警时间 | 用户名 | 告警类型 | 告警消息 | 严重程度 | 状态
- 无边框表格，仅行底线，hover 行高亮
- 状态标签使用胶囊形 Pill：

| 标签 | 背景 | 文字 |
|------|------|------|
| 正常 / resolved | `#dcfce7` | `#166534` |
| 可疑 / pending | `#fef3c7` | `#92400e` |
| 危险 / high | `#fee2e2` | `#991b1b` |
| 处理中 / acknowledged | `#e0e7ff` | `#3730a3` |
| 频率异常 | `#fef3c7` | `#92400e` |
| 设备异常 | `#e0e7ff` | `#3730a3` |
| 位置异常 | `#fee2e2` | `#991b1b` |

---

## 4. 组件风格规范

### 4.1 按钮

| 类型 | 背景 | 文字 | 边框 | Hover |
|------|------|------|------|-------|
| 主要按钮 | `#2563eb` | white | 无 | `#3b82f6` |
| 次要按钮 | white | `#374151` | `#d1d5db 1px` | bg:`#f9fafb` |
| 危险按钮 | white | `#ef4444` | `#fca5a5 1px` | bg:`#fef2f2` |
| 文字按钮 | transparent | `#2563eb` | 无 | `underline` |

统一规格：height 36px · border-radius 8px · font 14px/400
含图标按钮：gap 6px，图标 16px

### 4.2 输入框

- height 36px（带标签场景）或 40px（单独使用）
- padding 0 12px · border-radius 8px · border `#d1d5db`
- focus: border `#2563eb` · outline none
- placeholder color `#9ca3af`

### 4.3 表格

- 无边框，仅 `thead` 底部 `#e5e7eb` + `tbody tr` 底部 `#f3f4f6`
- thead: font 13px/500 color `#6b7280`
- tbody: font 14px/400 color `#111827`
- tr hover: background `#f3f4f6`
- td padding: 12px

### 4.4 统计卡片

- 白底 `#ffffff` + 边框 `#e5e7eb 1px` + border-radius 10px
- padding 20px
- 标签：13px/400 `#6b7280` · 数字：28px/700 `#111827`
- 趋势指示：13px/400，绿色 `#10b981` 或红色 `#ef4444`

### 4.5 状态标签（Pill）

```css
padding: 2px 10px;
border-radius: 999px;
font-size: 12px;
font-weight: 400;
```

---

## 5. 前端实现方案

### 5.1 全局样式覆盖

在 `App.vue` 或新建 `styles/global.css` 中覆盖 Element Plus 主题变量：

```css
/* 覆盖 Element Plus 主题色 */
:root {
  --el-color-primary: #2563eb;
  --el-color-primary-light-3: #3b82f6;
  --el-color-success: #10b981;
  --el-color-warning: #f59e0b;
  --el-color-danger: #ef4444;
  --el-bg-color: #f8f9fa;
  --el-border-color: #e5e7eb;
  --el-border-color-light: #d1d5db;
  --el-text-color-primary: #111827;
  --el-text-color-secondary: #6b7280;
  --el-text-color-placeholder: #9ca3af;
  --el-font-size-base: 14px;
  --el-font-weight-primary: 400;
  --el-border-radius-base: 8px;
  --el-border-radius-small: 6px;
}
```

### 5.2 Button 统一样式

```css
/* 覆盖 Element Plus 按钮默认字体 */
.el-button {
  font-weight: 400;
  font-size: 14px;
  --el-button-font-weight: 400;
}
```

### 5.3 路由与页面

| 路由 | 页面 | 当前状态 |
|------|------|----------|
| `/login` | 登录页 | ⚠️ 需优化 |
| `/` | Dashboard | ⚠️ 需优化 |
| `/login-logs` | 登录日志列表 | ❌ 未创建 |
| `/alerts` | 告警列表 | ❌ 未创建 |

### 5.4 字体引入

在 `index.html` 中添加 Google Fonts 引入：

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

### 5.5 实施优先级

1. 全局样式变量 + 字体引入（`index.html` + `App.vue`）
2. MainLayout 侧栏/顶栏样式更新
3. Login 页面优化
4. Dashboard 页面优化
5. 登录日志列表页（设计待补充）
6. 告警列表页（设计待补充）

---

## 6. 设计确认清单

- [x] 设计方向：方向 B — 极简白+浅灰
- [x] 色彩体系：深蓝侧栏 `#1a1a2e` + 白色内容 + 蓝色主交互
- [x] 字体体系：Inter + Noto Sans SC，按钮与正文统一 14px/400w
- [x] 间距体系：4px 基准递进
- [x] 侧边栏导航：深蓝背景 + 活跃项高亮 + 告警角标
- [x] Dashboard：4 卡 + 2:1 图表 + 告警表格
- [x] 登录页：居中卡片 + 完整状态覆盖
- [x] 组件规范：按钮/输入框/表格/标签