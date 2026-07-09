# 校园监测平台 UI 设计规范

> 版本: 1.0
> 更新日期: 2026-07-07
> 参考风格: Trueform CRM / Linear / Notion

---

## 1. 配色系统

### 主色调

| 名称 | 色值 | 用途 |
|------|------|------|
| **主色** | `#111827` | 标题、重要文字、按钮背景、侧边栏选中状态 |
| **主色浅** | `#374151` | 主色悬停状态、次要强调 |
| **主色更浅** | `#6B7280` | 正文、图标、次要信息 |

### 背景色

| 名称 | 色值 | 用途 |
|------|------|------|
| **页面背景** | `#F9FAFB` | 整体页面背景 |
| **卡片背景** | `#FFFFFF` | 卡片、弹窗、浮层 |
| **侧边栏背景** | `#FFFFFF` | 导航侧边栏 |
| **输入框背景** | `#FFFFFF` | 表单输入框 |
| **悬停背景** | `#F3F4F6` | 列表悬停、按钮悬停 |

### 文字颜色

| 名称 | 色值 | 用途 |
|------|------|------|
| **主文字** | `#111827` | 大标题、重要文字 |
| **次文字** | `#374151` | 正文、标签 |
| **辅助文字** | `#6B7280` | 说明文字、图标 |
| **禁用文字** | `#9CA3AF` | 占位符、禁用状态 |
| **反色文字** | `#FFFFFF` | 深色背景上的文字 |

### 边框与分割

| 名称 | 色值 | 用途 |
|------|------|------|
| **主边框** | `#E5E7EB` | 卡片边框、分割线 |
| **浅边框** | `#F3F4F6` | 表单边框、内部分割 |

### 状态色

| 名称 | 色值 | 用途 |
|------|------|------|
| **成功** | `#10B981` | 正向指标、成功提示 |
| **成功浅** | `#D1FAE5` | 成功背景、徽章 |
| **警告** | `#F59E0B` | 告警、需要注意 |
| **警告浅** | `#FEF3C7` | 警告背景、徽章 |
| **危险** | `#EF4444` | 错误、删除操作 |
| **危险浅** | `#FEE2E2` | 错误背景 |
| **信息** | `#3B82F6` | 提示信息 |
| **信息浅** | `#DBEAFE` | 信息背景 |

---

## 2. 字体系统

### 字体栈

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
  'Helvetica Neue', Arial, 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', sans-serif;
```

### 字号层级

| 层级 | 大小 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| **Display** | 32px | 700 | 1.2 | 页面大标题、数据指标 |
| **Heading** | 24px | 600 | 1.3 | 区块标题 |
| **Title** | 18px | 600 | 1.4 | 卡片标题、小标题 |
| **Subtitle** | 14px | 500 | 1.5 | 标签、小标题（大写或灰色） |
| **Body** | 14px | 400 | 1.5 | 正文、描述 |
| **Caption** | 12px | 400 | 1.5 | 辅助说明、时间戳 |

### 字重规范

| 字重 | 值 | 用途 |
|------|-----|------|
| **Regular** | 400 | 正文、描述 |
| **Medium** | 500 | 按钮、标签、导航 |
| **Semibold** | 600 | 标题、强调 |
| **Bold** | 700 | 大数字、Display |

### 文字样式示例

```css
/* 页面标题 */
.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #111827;
}

/* 卡片标题 */
.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

/* 区块标签（大写） */
.section-label {
  font-size: 14px;
  font-weight: 500;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* 正文 */
.body-text {
  font-size: 14px;
  font-weight: 400;
  color: #374151;
  line-height: 1.5;
}

/* 辅助文字 */
.caption {
  font-size: 12px;
  font-weight: 400;
  color: #9CA3AF;
}
```

---

## 3. 间距与留白

### 页面间距

| 名称 | 值 | 用途 |
|------|-----|------|
| **页面边距** | 32px | 页面内容与边缘的距离 |
| **页面边距（移动端）** | 24px | 小屏幕下的页面边距 |

### 组件间距

| 名称 | 值 | 用途 |
|------|-----|------|
| **区块间距** | 32px | 大区块之间的距离 |
| **卡片间距** | 24px | 卡片网格之间的间距 |
| **元素间距** | 16px | 表单元素、列表项之间的间距 |
| **紧凑间距** | 12px | 按钮组、标签组 |
| **微小间距** | 8px | 图标与文字、内联元素 |

### 内边距

| 名称 | 值 | 用途 |
|------|-----|------|
| **卡片内边距** | 24px | 卡片内部填充 |
| **卡片头部内边距** | 20px 24px | 卡片标题区域 |
| **按钮内边距** | 0 20px | 按钮水平内边距 |
| **输入框内边距** | 0 16px | 输入框水平内边距 |
| **列表项内边距** | 16px | 列表项上下内边距 |
| **紧凑内边距** | 12px | 小卡片、标签 |

### 间距组合示例

```css
/* 标准卡片 */
.card {
  padding: 24px;
  margin-bottom: 24px;
}

/* 页面容器 */
.page-container {
  padding: 32px;
}

/* 表单组 */
.form-group {
  margin-bottom: 20px;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 32px;
}
```

---

## 4. 组件样式

### 按钮

#### 主按钮

```css
.btn-primary {
  height: 40px;
  padding: 0 20px;
  background: #111827;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: #374151;
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
```

#### 次要按钮

```css
.btn-secondary {
  height: 40px;
  padding: 0 20px;
  background: transparent;
  color: #374151;
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
}

.btn-secondary:hover {
  background: #F9FAFB;
  border-color: #D1D5DB;
}
```

#### 图标按钮

```css
.btn-icon {
  width: 40px;
  height: 40px;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6B7280;
  transition: all 0.2s ease;
}

.btn-icon:hover {
  background: #F3F4F6;
  color: #111827;
}
```

### 卡片

#### 标准卡片

```css
.card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
```

#### 统计卡片

```css
.stat-card {
  background: #FFFFFF;
  border: 1px solid #E5E7EB;
  border-radius: 16px;
  padding: 24px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}
```

### 导航栏

#### 侧边栏

```css
.sidebar {
  width: 260px;
  background: #FFFFFF;
  border-right: 1px solid #E5E7EB;
  display: flex;
  flex-direction: column;
}

.sidebar.collapsed {
  width: 72px;
}
```

#### 导航项

```css
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  margin: 4px 12px;
  border-radius: 10px;
  color: #6B7280;
  font-weight: 500;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: #F3F4F6;
  color: #111827;
}

.nav-item.active {
  background: #F3F4F6;
  color: #111827;
  font-weight: 600;
}
```

#### 顶部栏

```css
.top-bar {
  height: 72px;
  background: #FFFFFF;
  border-bottom: 1px solid #E5E7EB;
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
```

### 输入框

```css
.input-wrapper {
  position: relative;
}

.form-input {
  width: 100%;
  height: 48px;
  padding: 0 16px 0 44px;
  border: 1px solid #E5E7EB;
  border-radius: 10px;
  font-size: 14px;
  color: #111827;
  background: #FFFFFF;
  transition: all 0.2s ease;
}

.form-input:focus {
  outline: none;
  border-color: #111827;
  box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.1);
}

.form-input::placeholder {
  color: #9CA3AF;
}
```

### 表格

```css
.table {
  width: 100%;
  border-collapse: collapse;
}

.table th {
  padding: 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #F9FAFB;
  border-bottom: 1px solid #E5E7EB;
}

.table td {
  padding: 16px;
  border-bottom: 1px solid #F3F4F6;
}

.table tr:hover {
  background: #F9FAFB;
}
```

### 标签/徽章

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.badge-success {
  background: #D1FAE5;
  color: #10B981;
}

.badge-warning {
  background: #FEF3C7;
  color: #F59E0B;
}

.badge-danger {
  background: #FEE2E2;
  color: #EF4444;
}
```

---

## 5. 布局规范

### 页面结构

```
┌─────────────────────────────────────────┐
│  侧边栏 (260px)  │  顶部栏 (72px)        │
│                  ├───────────────────────┤
│  Logo            │                       │
│  ─────────────── │  页面内容            │
│  导航项          │  (padding: 32px)     │
│  导航项          │                       │
│  导航项          │  ┌─────────────────┐  │
│                  │  │   卡片/内容      │  │
│                  │  └─────────────────┘  │
│                  │                       │
└──────────────────┴───────────────────────┘
```

### 响应式断点

| 断点 | 宽度 | 调整 |
|------|------|------|
| **桌面** | > 1024px | 完整侧边栏 + 三列网格 |
| **平板** | 768-1024px | 收起侧边栏 + 两列网格 |
| **移动** | < 768px | 隐藏侧边栏 + 单列布局 |

---

## 6. 图标使用

使用 **Element Plus Icons**:

```javascript
import {
  Monitor,           // 仪表盘
  Document,          // 文档/日志
  WarningFilled,     // 告警
  ArrowDown,         // 下拉箭头
  Expand,            // 展开
  Fold,              // 收起
  SwitchButton,      // 退出/电源
  User,              // 用户
  Lock,              // 锁定/密码
  Check,             // 勾选
  Warning,           // 警告
  TrendCharts,       // 趋势图表
  Refresh,           // 刷新
} from '@element-plus/icons-vue'
```

---

## 7. 设计原则

1. **简洁至上**: 去除多余装饰，留白充足
2. **层次分明**: 通过字号、字重、颜色建立清晰层级
3. **一致性**: 所有组件遵循统一规范
4. **反馈及时**: 悬停、点击、加载状态明确
5. **可读性**: 文字与背景对比度充足

---

## 8. 快速参考

### 创建新页面检查清单

- [ ] 使用正确的配色（主色 `#111827`、背景 `#F9FAFB`）
- [ ] 遵循字号层级（Display/Heading/Title/Body）
- [ ] 使用标准间距（页面 32px、卡片 24px、元素 16px）
- [ ] 卡片圆角 12px、按钮圆角 8px
- [ ] 添加适当的悬停效果
- [ ] 确保响应式适配

### 常用组合

```vue
<!-- 统计卡片 -->
<div class="stat-card">
  <div class="stat-header">
    <span class="section-label">今日登录</span>
    <div class="stat-badge success">
      <el-icon><TrendCharts /></el-icon>
    </div>
  </div>
  <div class="stat-value">1,234</div>
  <div class="stat-footer">
    <span class="stat-trend positive">+12%</span>
    <span class="caption">较昨日</span>
  </div>
</div>
```