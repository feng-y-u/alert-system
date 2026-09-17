# 13. API 文档 ｜ 16. 第三方服务

## 13.1 通用约定

| 项 | 值 | 依据 |
|---|---|---|
| 基础前缀 | `/api`（变量名为 `API_V1_PREFIX`，**值不是 `/api/v1`**） | `core/config.py:8`、`main.py:29-35` |
| 交互式文档 | `/docs`（Swagger UI）、`/redoc` | `main.py:17-18` |
| 请求/响应编码 | JSON（`Content-Type: application/json`） | FastAPI 默认 |
| 鉴权矩阵 | 见 §13.2 | `core/deps.py`、`api/notifications.py` |
| 错误响应体 | FastAPI 标准 `{"detail": "..."}`；参数校验失败为 `{"detail":[{...}]}` | 实测（`tests/test_integration.py` 断言 401/422） |
| CORS | `allow_origins=["*"]`、`allow_credentials=True`、方法/头全放开 | `main.py:21-27` |
| 分页风格 | 偏移分页 `skip`/`limit`，响应统一 `{items,total,skip,limit}` | `schemas/logs_query.py:27-32`、`schemas/alert.py:33-37` |
| 字段命名 | 多数接口 snake_case；**统计接口为 camelCase** | `api/stats.py:56-61` |

> **示例数据说明**：下文的请求/响应示例是**依据 Pydantic 模型与源码逻辑构造的**（字段名、类型、必填性均可在源码核对），**非抓取的真实响应**——本次审计环境未运行 Docker/MySQL，无法产生真实报文。示例中的时间、ID 均为占位。

## 13.2 鉴权方式

| 方式 | 适用接口 | 实现 | 失败响应 |
|---|---|---|---|
| 无 | `GET /api/health` | — | — |
| `X-API-Key: <settings.API_KEY>` | `POST /api/logs` | `core/deps.py:62-69` | 401 `Invalid API Key`；缺头 422 |
| `Authorization: Bearer <jwt>` | 其余全部管理端接口 | `core/deps.py:13-59` | 401（无凭证/无效/过期/用户不存在）；400（`is_active=False`） |
| query `?token=<jwt>` | `GET /api/notifications/stream` | `api/notifications.py:13-28` | 401 |

JWT 载荷：`{"sub": "<user_id>", "exp": <UTC 时间>}`（`core/security.py:21-27`），HS256，默认有效期 1440 分钟（`config.py:14`）。

---

## 13.3 端点详解

### 13.3.1 `GET /api/health`

| 项 | 内容 |
|---|---|
| 功能 | 存活探针，无鉴权 |
| 参数 | 无 |
| 响应 | `{"status":"ok","message":"服务运行正常"}`（**裸 dict，非 Pydantic 模型**） |
| 状态码 | 200（无失败分支） |
| 源码 | Router：`api/health.py:6-8`；无 Service/Model |

### 13.3.2 `POST /api/auth/login`

| 项 | 内容 |
|---|---|
| 功能 | 管理员登录，签发 JWT |
| 鉴权 | 无（公开） |
| 请求体 | `UserLogin`：`username: str`(必填)、`password: str`(必填)（`schemas/user.py:12-14`） |
| 响应 | `Token`：`access_token: str`、`token_type: str = "bearer"`（`schemas/user.py:28-30`） |
| 状态码 | 200 成功；401 用户名或密码错误 / 用户被禁用；422 缺字段 |
| 调用链 | `api/auth.py:14-25` → `services/auth.py:14-22`（`User` 查询 + `verify_password`）→ `core/security.py:21-27` |
| 源码位置 | Router `api/auth.py:14`；Service `services/auth.py:14`；Model `models/user.py:12` |

请求示例（schema 推导）：
```json
{ "username": "admin", "password": "<YOUR_PASSWORD>" }
```
响应示例（schema 推导）：
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

### 13.3.3 `POST /api/auth/register`

| 项 | 内容 |
|---|---|
| 功能 | 创建新管理员（**仅已登录管理员可调用**） |
| 鉴权 | Bearer JWT |
| 请求体 | `UserCreate`：`username`、`email`、`password`（均必填，**无格式/强度校验**） |
| 响应 | `UserResponse`：`id`、`username`、`email`、`role`、`is_active`、`created_at` |
| 状态码 | 200 成功；400 用户名已存在 / 邮箱已被使用；401 未登录；422 缺字段 |
| 调用链 | `api/auth.py:28-39` → `services/auth.py:25-42`（两次唯一性查询 → `get_password_hash` → commit） |
| 备注 | 无角色校验分支：任何已登录且启用的用户都可创建管理员（当前所有用户 `role` 均为 `admin`） |

### 13.3.4 `GET /api/auth/me`

| 项 | 内容 |
|---|---|
| 功能 | 返回当前登录用户 |
| 鉴权 | Bearer JWT |
| 参数 | 无 |
| 响应 | `UserResponse` |
| 状态码 | 200；401；400（用户被禁用） |
| 源码 | `api/auth.py:42-45` → `core/deps.py:50-59` |
| 备注 | **两个管理端都未调用此端点**（📄），因此前端不做会话有效性校验，仅在首个业务请求 401 时才发现 token 失效 |

### 13.3.5 `POST /api/logs`

| 项 | 内容 |
|---|---|
| 功能 | 接收被监控系统上报的登录日志，落库后触发异步异常检测 |
| 鉴权 | `X-API-Key` |
| 请求体 | `LoginLogCreate`：`username: str`(**必填**)、`login_time: datetime`(**必填**)、`ip_address: str`(**必填**)、`user_agent: str \| None = None`、`login_status: str`(**必填、无取值约束**)、`location: str \| None = None` |
| 响应 | `LoginLogResponse`：`id`、`username`、`login_time`、`ip_address`、`user_agent`、`login_status`、`location`、`created_at` |
| 状态码 | **201** 成功（`api/logs.py:15` 显式声明）；401 API Key 错误；422 缺必填字段或缺 API Key 头 |
| 调用链 | `api/logs.py:15-22` → `core/deps.py:62-69` → `services/logs.py:49-60` → 写库 → `tasks/detection.py:50` 投递 |
| 源码位置 | Router `api/logs.py:15`；Service `services/logs.py:49`；Model `models/login_log.py:12`；Schema `schemas/login_log.py:6` |
| ⚠️ 运行期风险 | Redis 不可用时会**无限阻塞**（实测，见 `11-性能分析.md` PERF-00）；`login_status` 取值建议统一（见 §13.5） |

请求示例（schema 推导）：
```json
{
  "username": "student01",
  "login_time": "2026-09-16T09:30:00+00:00",
  "ip_address": "10.0.0.1",
  "user_agent": "Mozilla/5.0",
  "login_status": "success",
  "location": "教学楼A"
}
```
响应示例（schema 推导，HTTP 201）：
```json
{
  "id": 1,
  "username": "student01",
  "login_time": "2026-09-16T09:30:00",
  "ip_address": "10.0.0.1",
  "user_agent": "Mozilla/5.0",
  "login_status": "success",
  "location": "教学楼A",
  "created_at": "2026-09-16T09:30:01"
}
```

### 13.3.6 `GET /api/logs`

| 项 | 内容 |
|---|---|
| 功能 | 分页查询登录日志 |
| 鉴权 | Bearer JWT |
| Query 参数 | `username`（模糊 `LIKE %x%`）、`ip_address`（精确）、`login_status`（**正则 `^(success\|failure)$`**）、`start_time`、`end_time`（ISO 时间）、`skip`(≥0，默认 0)、`limit`(1–100，默认 50)（`schemas/logs_query.py:9-24`） |
| 响应 | `LogListResponse`：`{items: [LoginLogResponse], total, skip, limit}` |
| 状态码 | 200；401；**422**（`login_status` 非 `success`/`failure`，或 `start_time > end_time`） |
| 排序 | 固定 `login_time DESC`，**无排序参数** |
| 调用链 | `api/logs.py:25-47` → `services/logs.py:36-46` → `build_log_query`（`:11-33`） |
| ⚠️ 契约破损 | `monitored-app` 上报的是 `failed`，用 `?login_status=failed` 查询将返回 422（见 `14-评估与改进.md`） |

### 13.3.7 `DELETE /api/logs`

| 项 | 内容 |
|---|---|
| 功能 | **清空全部登录日志** |
| 鉴权 | Bearer JWT |
| 参数 | 无（无 scope、无确认） |
| 响应 | `{"deleted": <int>}` |
| 状态码 | 200；401 |
| 源码 | `api/logs.py:50-58`（`db.query(LoginLog).delete()` + commit） |
| ⚠️ 风险 | 物理删除、无软删除、无审计；且 `alerts.log_id` 外键**无级联**，存在告警引用时该删除会因外键约束失败（分析结论，未在 MySQL 实测） |

### 13.3.8 `GET /api/alerts`

| 项 | 内容 |
|---|---|
| 功能 | 分页查询告警 |
| 鉴权 | Bearer JWT |
| Query 参数 | `status`（`pending`/`acknowledged`/`resolved`，**描述性，无校验**）、`severity`（`low`/`medium`/`high`，无校验）、`username`（**精确等值**，非模糊）、`skip`(≥0)、`limit`(1–100)（`api/alerts.py:18-22`） |
| 响应 | `AlertListResponse`：`{items:[AlertResponse], total, skip, limit}`；`AlertResponse` 字段：`id`、`username`、`log_id`、`alert_type`、`alert_message`、`severity`、`status`、`created_at`、`updated_at`、`resolved_at` |
| 状态码 | 200；401；422（分页越界） |
| 排序 | `created_at DESC`，无次级排序键 |
| 源码 | `api/alerts.py:16-44`；无 Service 层，直接查 `models/alert.py:13` |

### 13.3.9 `GET /api/alerts/{alert_id}`

| 项 | 内容 |
|---|---|
| 功能 | 获取单条告警详情 |
| 鉴权 | Bearer JWT |
| 路径参数 | `alert_id: int` |
| 响应 | `AlertResponse` |
| 状态码 | 200；404 `"Alert not found"`；401；422（非整数） |
| 源码 | `api/alerts.py:47-57` |
| 备注 | 两个管理端均未使用（📄） |

### 13.3.10 `PUT /api/alerts/{alert_id}`

| 项 | 内容 |
|---|---|
| 功能 | 更新告警状态 |
| 鉴权 | Bearer JWT |
| 请求体 | `AlertUpdate`：`status: str`（**无枚举约束**） |
| 行为 | 设置 `status`；仅当新值为 `resolved` 时写 `resolved_at = now(UTC)`（`api/alerts.py:73-76`） |
| 响应 | `AlertResponse` |
| 状态码 | 200；404；401；422 |
| 源码 | `api/alerts.py:60-80` |
| ⚠️ 风险 | ① 任意字符串可入库（含拼写错误的状态）；② 从 `resolved` 回退到其他状态时 `resolved_at` **不被清空**，数据自相矛盾；③ 无状态机校验（任意状态可跳到任意状态） |

### 13.3.11 `DELETE /api/alerts`

| 项 | 内容 |
|---|---|
| 功能 | 清空告警（全部或已处理） |
| 鉴权 | Bearer JWT |
| Query 参数 | `scope`（**必填**，`Literal["all","processed"]`）；`processed` = `status in (acknowledged, resolved)` |
| 响应 | `{"deleted": <int>, "scope": "<scope>"}` |
| 状态码 | 200；401；**422**（缺 `scope` 或值非法） |
| 源码 | `api/alerts.py:83-96`（`delete(synchronize_session=False)`） |
| ⚠️ 风险 | 物理删除、无审计、无软删除；删除后关联的 `login_logs` 保留，`pending` 告警在 `scope=processed` 下不受影响 |

### 13.3.12 `GET /api/stats`

| 项 | 内容 |
|---|---|
| 功能 | 仪表盘总览指标 |
| 鉴权 | Bearer JWT |
| Query 参数 | `days: int = 7`（**无范围校验**） |
| 响应 | `{todayLogins:int, pendingAlerts:int, activeUsers:int, loginTrend:[{date:"MM-DD", count:int}]}`（camelCase 裸 dict） |
| 状态码 | 200；401 |
| 日界语义 | 使用 **UTC** 零点（`api/stats.py:23-24`）；Celery 却配 `Asia/Shanghai`（`tasks/__init__.py:15`）→ 与本地时间差 8 小时 |
| 源码 | `api/stats.py:16-61` |
| ⚠️ 性能 | `days` 次独立 COUNT 查询，且无上限（见 `11-性能分析.md` PERF-01） |

### 13.3.13 `GET /api/stats/alerts`

| 项 | 内容 |
|---|---|
| 功能 | 告警维度统计（趋势/类型分布/级别分布） |
| 鉴权 | Bearer JWT |
| Query 参数 | `days: int = 7`，**校验 `1..365`**，越界返回 400 `"days must be between 1 and 365"` |
| 响应 | `{alertTrend:[{date,count}], typeDist:[{name,value}], severityDist:[{name,value}]}` |
| 状态码 | 200；400；401 |
| 源码 | `api/stats.py:64-111` |
| 备注 | 分布统计口径为「窗口起点之后」，而趋势为逐日窗口，二者边界不完全对齐（`:78,97,103`） |

### 13.3.14 `GET /api/notifications/stream`

| 项 | 内容 |
|---|---|
| 功能 | SSE 实时告警推送 |
| 鉴权 | **query 参数 `token=<jwt>`**（`EventSource` 无法自定义请求头，属有意设计） |
| 参数 | `token`（必填） |
| 响应 | `Content-Type: text/event-stream`；事件帧 `data: {"alert_id":..,"type":..,"severity":..,"username":..}\n\n`；空转时 `: heartbeat\n\n` |
| 状态码 | 200（建流）；401（token 无效/用户不存在/已禁用） |
| 源码 | `api/notifications.py:31-61`；事件来源 `tasks/detection.py:16-27`；Redis 频道 `alerts` |
| ⚠️ 风险 | ① token 出现在 URL（访问日志/浏览器历史）；② 请求级 DB 会话被持有至流结束（连接池占用）；③ `except Exception: pass` 静默终止流，客户端只能靠 onerror 感知 |

### 13.3.15 `GET /api/settings/email`

| 项 | 内容 |
|---|---|
| 功能 | 查看邮件配置状态（**不返回任何凭据**） |
| 鉴权 | Bearer JWT |
| 响应 | `EmailConfigStatus`：`configured: bool`、`host: str`、`port: int`、`has_user: bool`、`from_addr: str`、`note: str` |
| 状态码 | 200；401 |
| 源码 | `api/settings.py:19-37`；判定逻辑 `tasks/email.py:30-36` |
| note 文案 | 未配置时：`EMAIL_USER 为空，请在 .env 中设置` 或 `使用了占位配置（example），请填写真实 SMTP 凭据` |

### 13.3.16 `POST /api/settings/email/test`

| 项 | 内容 |
|---|---|
| 功能 | 发送测试邮件，用于诊断 SMTP 凭据 |
| 鉴权 | Bearer JWT |
| 请求体 | 无 |
| 响应 | `EmailTestResult`：`success: bool`、`message: str` |
| 失败分类 | 未配置 → `success=false`；无活跃管理员邮箱 → 提示；`SMTPAuthenticationError` → 账号/授权码错误；`SMTPException` → 发送失败；`OSError` → 无法连接（15s 超时） |
| 状态码 | 200（业务失败也返回 200 + `success=false`）；401 |
| 源码 | `api/settings.py:40-77`（同步 `smtplib.SMTP_SSL`，FastAPI 以 `def` 形式将其放入线程池执行） |
| 备注 | 与 `tasks/email.py:39-56` 的邮件构造实现不一致（此处手工拼 MIME 字符串） |

---

## 13.4 调用流程汇总（Router → Service → Model）

| 端点 | Router | Service / 业务函数 | Model / 表 |
|---|---|---|---|
| `POST /auth/login` | `api/auth.py:14` | `services/auth.py:14` | `users` |
| `POST /auth/register` | `api/auth.py:28` | `services/auth.py:25` | `users` |
| `GET /auth/me` | `api/auth.py:42` | `core/deps.py:50` | `users` |
| `POST /logs` | `api/logs.py:15` | `services/logs.py:49` → `tasks/detection.py:50` | `login_logs` → `alerts` |
| `GET /logs` | `api/logs.py:25` | `services/logs.py:36` + `:11` | `login_logs` |
| `DELETE /logs` | `api/logs.py:50` | 直接 ORM 删除 | `login_logs` |
| `GET /alerts` | `api/alerts.py:16` | **无 Service（直接查询）** | `alerts` |
| `GET /alerts/{id}` | `api/alerts.py:47` | 同上 | `alerts` |
| `PUT /alerts/{id}` | `api/alerts.py:60` | 同上 | `alerts` |
| `DELETE /alerts` | `api/alerts.py:83` | 同上 | `alerts` |
| `GET /stats` | `api/stats.py:16` | 内联聚合 | `login_logs`、`alerts` |
| `GET /stats/alerts` | `api/stats.py:64` | 内联聚合 | `alerts` |
| `GET /notifications/stream` | `api/notifications.py:31` | 内联 SSE | `users`（校验）|
| `GET /settings/email` | `api/settings.py:19` | `tasks/email.py:30` | — |
| `POST /settings/email/test` | `api/settings.py:40` | `tasks/email.py:19,30` | `users`（收件人）|

**结构观察（分析结论）**：`alerts` 与 `stats` 两组接口**没有 service 层**，业务逻辑直接写在 router 中；而 `logs`/`auth`/`detection` 有 service 层。这种不一致会让「业务逻辑该放哪」缺乏统一答案。

## 13.5 `login_status` 取值现状（契约风险）

| 出处 | 值 | 位置 |
|---|---|---|
| 查询参数正则 | `success` \| `failure` | `schemas/logs_query.py:13` |
| Vue 下拉选项 | `success` / `failure` | `frontend/src/components/logs/LogFilter.vue:21-22` |
| Vue 状态标签映射 | `success` / `failure` | `frontend/src/components/common/StatusTag.vue:25,32` ✅已核实 |
| 种子脚本 | `success` / `failure` | `scripts/seed_logs.py:44` |
| Mock 数据脚本 | `success` / `failure` | `scripts/generate_mock_data.py:65` |
| 检测脚本 | `success` | `scripts/detection_smoke.py:35,79` |
| **仿真器上报** | **`failed`** | `monitored-app/app.py:64,106,125` |
| Flutter 客户端 | 只认 `failure`（📄） | `flutter_app/lib/services/logs_service.dart:21-22` |

结论：词表以 `success`/`failure` 为准，**`monitored-app` 的 `failed` 是唯一的离群值**，会造成「数据能入库但筛选不出」。

---

## 16. 第三方服务

本项目的「外部依赖」几乎全部由 Docker Compose 自建，真正的外部第三方服务只有 SMTP 邮箱。

| 服务 | 用途 | 配置项 | 是否必需 | 源码 |
|---|---|---|---|---|
| MySQL 8.0 | 主数据存储 | `DATABASE_URL` | **必需** | `docker-compose.yml:4-22`、`core/database.py:6` |
| Redis 7 | Celery broker/backend、pub/sub、检测游标 | `REDIS_URL` | **必需**（缺失时上报接口阻塞） | `docker-compose.yml:24-37`、`tasks/__init__.py:6-7` |
| SMTP 邮箱服务 | 告警邮件通知 | `EMAIL_HOST/PORT/USER/PASSWORD`、`ALERT_EMAIL_FROM` | 可选（未配置则跳过） | `tasks/email.py:30-36,83` |
| Docker Hub / 阿里云 PyPI 镜像 | 镜像与依赖拉取 | `Dockerfile:3` 配置 `mirrors.aliyun.com` | 构建期 | `backend/Dockerfile:3` |
| npm 镜像 `registry.npmmirror.com` | 前端依赖拉取 | `frontend/Dockerfile:5` | 构建期 | `frontend/Dockerfile:5` |
| Google Fonts（外链） | 前端字体 | 无配置项（HTML 外链，📄） | 可选 | 📄 `frontend/index.html` |
| 公网 IP 库 / 地理位置服务 | — | **源码中未发现**：`location` 字段由上报方填写，代码中无任何 IP 归属地查询 | — | `scripts/seed_logs.py:73` 注释「地理位置字段已弃用」 |

**未使用的第三方依赖**：`pandas`、`numpy` 在 `requirements.txt:19-20` 声明，但全后端 Python 代码**零引用**（实测 grep）；`docs/DESIGN.md:52,141` 声称使用 Pandas 做分析，属文档与实现不符。

**无 CI/CD、无外部监控/APM、无错误追踪服务**：实测 `.github/`、`.gitlab-ci.yml`、`.pre-commit-config.yaml` 均不存在；代码中亦无 Sentry/OpenTelemetry 之类 SDK（`grep` 无命中）。

**邮件服务的经验性约束（来自项目内文档）**：163 邮箱必须使用 `465 + SMTP_SSL`（`AGENTS.md`），代码强制 `smtplib.SMTP_SSL`（`tasks/email.py:83`、`api/settings.py:53`），与之一致；`.env.example` 默认端口亦是 465。
