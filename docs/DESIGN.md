# 详细设计方案

**校园账号异常登录监测与告警平台** — 详细设计文档

> 核心框架信息（技术栈、项目结构、命令等）请参考 [CLAUDE.md](../CLAUDE.md)  
> UI 设计规范请参考 [UI.md](UI.md)

---

## 项目定位

监控/运维类平台，接收校园系统的登录日志，检测异常登录行为并产生告警，供管理员处理。

```
校园系统（被监控） → POST /api/logs → 本平台 → 检测异常 → 告警 → 管理员处理
```

| 角色 | 说明 |
|------|------|
| **管理员** | 使用本平台的人，登录后查看 Dashboard、日志、告警，并进行处理 |
| **校园系统用户** | 被监控系统的使用者（学生/教师），**不是本项目的用户**，他们的登录行为是监控数据来源 |

---

## 数据模型

### users（管理员表）
```
id, username, email, hashed_password, role(admin), is_active, created_at, updated_at
```

### login_logs（登录日志表）
```
id, username(被监控用户), login_time, ip_address, user_agent, login_status, location, created_at, updated_at
```

### alerts（告警表）
```
id, username(关联login_logs), log_id(可选,引用login_logs.id), alert_type(frequency/device), alert_message,
severity(low/medium/high), status(pending/acknowledged/resolved), created_at, updated_at, resolved_at
```

---

## 开发计划（8周）

| 周次 | 内容 | 状态 |
|------|------|------|
| 第1周 | 项目搭建：FastAPI框架 + MySQL/Redis + 基础模型 + Vue 3 + Docker | ✅ |
| 第2周 | 管理员认证：登录/注册 JWT API + seed 脚本 + 前端登录页 + 路由守卫 | ✅ |
| 第3周 | 登录日志管理：接收/查询 API + 模拟数据脚本 | ✅ |
| 第4周 | 异常检测：频率异常 + 设备异常 + Pandas 分析 | ✅ |
| 第5周 | 告警系统：生成/查询 API + 邮件通知 | ✅ |
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ✅ |
| 第7周 | 功能完善：实时通知 + 优化 + 错误处理 | ✅ |
| 第8周 | 测试与部署：集成测试 + Docker 部署 + 文档 | ✅ |

### 后续扩展
地理位置检测（IP库 → `location` 类型告警）、WebSocket 实时监控、告警规则配置界面、移动端适配

---

## 鉴权设计

本平台有**两套独立鉴权**，分别用于不同接口，不要混用：

| 接口类型 | 鉴权方式 | 关键依赖 | 代码位置 |
|---|---|---|---|
| 日志接收 `POST /api/logs` | `X-API-Key` 请求头 | `verify_api_key` | `app/api/logs.py`、`app/core/deps.py` |
| 管理员接口（查询日志、告警 CRUD 等） | JWT Bearer Token | `get_current_active_user` | `app/core/deps.py` |

- 校园系统（被监控方）调用 `POST /api/logs` 时只需带 `X-API-Key: <API_KEY>`，无需登录；`API_KEY` 默认值见 `app/core/config.py`（生产必须改）。
- 管理员需先 `POST /api/auth/login` 拿 JWT，后续请求由前端 Axios 拦截器自动附加 `Authorization: Bearer <token>`。

---

## 异常检测规则

检测在 `app/services/detection.py` 实现，两种类型各有固定阈值与分档：

### 频率异常（`frequency`）
- 规则：同一用户 **5 分钟内登录 ≥ 10 次** 即为异常
- 严重级别：`medium`（10–30 次，提示"可能存在异常"）/ `high`（>30 次，提示"疑似暴力破解"）

### 设备异常（`device`）
- 规则：同一用户 **1 小时内出现 ≥ 2 个不同设备** 即为异常
  - "设备"按 `(user_agent, ip_address)` 组合去重统计
- 严重级别：`medium`（2 个设备）/ `high`（>2 个设备，提示"疑似账号共享或被盗"）

### 两种检测模式
按是否传入 `log_id` 区分（见 `detect_*_anomaly` 函数签名）：

| 模式 | 触发方式 | 时间窗口终点 | 调用示例 |
|---|---|---|---|
| 实时检测 | 日志写入后立即触发 | 以该条日志的 `login_time` 为终点 | 传 `log_id` |
| 定时检测 | Celery beat 定时触发 | 以 `datetime.utcnow()` 为终点 | 不传 `log_id` |

### 告警去重
新告警写入前先查 `should_create_alert`：若该用户 **24 小内已存在同类型 `pending` 告警**，则不再创建，避免告警风暴。

---

## 项目结构

```
backend/
├── app/
│   ├── api/           # API 路由（每个功能一个文件）
│   ├── core/          # 配置 + 数据库 + 安全 + 依赖注入
│   ├── models/        # SQLAlchemy ORM 模型
│   ├── schemas/       # Pydantic 请求/响应模式
│   ├── services/      # 业务逻辑
│   └── tasks/         # Celery 异步任务
├── alembic/           # 数据库迁移
├── tests/             # pytest 测试
├── scripts/           # 工具脚本（如 seed.py）
└── requirements.txt
frontend/
├── src/
│   ├── api/           # Axios 客户端
│   ├── layouts/       # 布局组件
│   ├── router/        # 路由配置
│   ├── stores/        # Pinia 状态管理
│   ├── views/         # 页面视图
│   └── components/    # Vue 组件
└── ...
```


## 注意事项

1. **角色区分** — 不要混淆"被监控用户"和"本平台管理员"
2. **数据隐私** — 登录日志含敏感信息，确保加密传输和存储
3. **异步处理** — 耗时操作（邮件、检测）使用 Celery 异步执行
4. **性能** — Pandas 分析大量日志时优先使用数据库查询优化

### 已知结构边界（当前规模暂不重构，扩展时再处理）

- **`core/` 职责集中** — `config / database / security / deps / redis` 五类职责同放 `app/core/`。当前文件均小、边界清晰，拆分成本高于收益；待引入"告警规则配置界面"等扩展、`core/` 显著膨胀后再拆分。
- **schema 直接用于 api 层响应** — service 返回 ORM 对象，由 Pydantic `response_model` + `from_attributes=True` 直接序列化，没有 service→DTO 转换层。当前 service 多为薄封装，引入 DTO 转换属 speculative abstraction；待出现 ORM 对象泄漏响应或 service 返回结构需稳定化的实际痛点时再加。