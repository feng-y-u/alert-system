# AGENTS.md

OpenCode / CodeBuddy 专用速查。与 `docs/tech/` 互补：本文件只记录**易踩坑、文档/config 不一致或需要交叉多处才能推断**的事实。本文件与 `docs/tech/` 冲突时以本文件为准（已验证代码）。

## 项目定位

**校园账号异常登录监测与告警平台** —— 安全审计与日志分析系统，**监控/运维类平台，不是面向师生的业务系统**。学术项目/毕业设计。

```
校园系统（被监控）→ POST 登录日志 → 本平台 → 检测异常 → 生成告警 → 管理员处理
```

管理员登录后台查看日志/告警，不管校园系统的业务。判断"这个功能该不该做"时先回到这条定位。

## 架构与检测链路（核心，跨 5 个文件）

后端分层：`api/ → schemas/（校验）→ services/（业务）→ models/（ORM）→ MySQL`，`tasks/` 为 Celery 异步侧支。

异常检测是本项目的心脏，链路分散在多个文件，改动前先看清全貌：

```
POST /api/logs  (X-API-Key 鉴权)
  └─ services/logs.py:create_log   落库 commit
       └─ detect_anomaly_for_log.delay(log.id)      ← 入口一：单条日志实时检测
            └─ tasks/detection.py
                 ├─ services/detection.py
                 │    ├─ detect_frequency_anomaly  5 分钟内同一用户 ≥10 次登录
                 │    └─ detect_device_anomaly     1 小时内同一用户 ≥2 个 (user_agent + ip) 组合
                 ├─ 严重级别：frequency 10~30 次 = medium，>30 = high；device 2 个 = medium，>2 = high
                 ├─ should_create_alert 去重：24h 内已有同 username + 同 alert_type 的 pending 告警则跳过
                 ├─ Alert 落库
                 ├─ send_alert_email.delay(alert.id)              邮件（未配置 SMTP 则跳过）
                 └─ Redis PUBLISH channel "alerts"                实时推送
                      └─ GET /api/notifications/stream?token=<jwt>  SSE
                           └─ frontend/src/stores/notification.js
```

**入口二**：Celery Beat 每小时跑 `run_anomaly_detection`（`app/tasks/__init__.py` 的 `beat_schedule`），增量扫描上次检测后新增的日志所属用户。游标存在 Redis 键 `anomaly_detection:last_check_time`（`tasks/detection.py`，默认回溯 1 小时）。它复用同一套 `services/detection.py`，但不传 `log_id`，因此时间窗口以 `datetime.now(UTC)` 为终点。

**最关键的坑（已修复，改动时勿回退）**：`create_log` 在请求线程内同步调用 `.delay()`。此前 Redis 不可用时，result backend 的 pubsub 消费端会无限重连，**把上报请求卡死**（实测 >300s 无返回）。现在 `tasks/__init__.py` 已设 `task_ignore_result=True` + 短连接超时 + 有限重试（实测约 4s 快速失败），并且 `create_log` 用 try/except 兜底：**投递失败不影响上报返回**，日志已经落库，并由每小时 Beat 增量扫描兜底补检。测试由 `tests/conftest.py` 的全局 autouse fixture 统一屏蔽投递。

## 认证矩阵（两套鉴权，各管一半接口）

| 场景 | 鉴权方式 | 实现 |
|---|---|---|
| 管理员 UI 的绝大多数接口 | `Authorization: Bearer <jwt>` | `core/deps.py:get_current_active_user` |
| 日志上报 `POST /api/logs` | `X-API-Key` 头 | `core/deps.py:verify_api_key`，比对 `settings.API_KEY` |
| SSE `/api/notifications/stream` | **query 参数 `?token=<jwt>`** | `api/notifications.py` 内自行 `decode_access_token` |
| `GET /api/health` | 无鉴权 | — |
| 修改自己的密码 `POST /api/auth/change-password` | Bearer JWT（用 `get_current_user`，刻意绕过改密拦截） | `api/auth.py` |
| 审计日志 `GET /api/audit-logs` | Bearer JWT | `api/audit.py` |

- `get_current_active_user` 还会拦截 `must_change_password=True` 的用户（**403**）：`scripts/seed.py` 创建的默认 `admin` 带此标记，**首次登录必须先改密**才能使用其它接口。
- 登录失败限流：同一「用户名 + 来源 IP」在窗口内失败达 `LOGIN_MAX_FAILURES`（默认 5）次返回 **429**；Redis 不可用时 fail-open 并熔断 30s（避免每次都等连接超时）。

SSE 用 query 传 token 不是设计瑕疵：浏览器 `EventSource` 无法附加自定义请求头，所以这里绕开了统一的 Bearer 依赖。改鉴权时别把它"统一"回 Bearer。

## 关键路径与端口

- **Redis 主机端口是 8880**（非 6379）。`docker-compose.yml` 把容器 6379 映射到主机 8880。
- **API 前缀是 `/api`，不是 `/api/v1`**。配置变量名 `API_V1_PREFIX` 但值是 `"/api"`。新增路由统一用 `prefix=settings.API_V1_PREFIX`。
- 后端 dev port **8001**，前端 Vite port **5173**，Vite 代理默认 `/api → http://localhost:8001`（可用 `VITE_DEV_PROXY_TARGET` 覆盖，例如改跑 Docker 后端时指向 `:8000`）。
- Docker Compose 主机端口：MySQL `8881`、Redis `8880`、Backend `8000`、Frontend `8882`（→容器 80）。
- **Docker 中 migration + seed 自动执行**（`docker-entrypoint.sh` 启动前先跑 `alembic upgrade head` + `python scripts/seed.py`）。
- 没有 CI、pre-commit、`opencode.json`。
- **Redis 在本项目有 3 类用途**，排查时别只想到 Celery：① Celery broker + result backend；② pub/sub 频道 `alerts`（SSE 数据源）；③ 键 `anomaly_detection:last_check_time`（增量检测游标）。

## 添加新功能的固定步骤（易漏）

1. 新模型必须在 `backend/app/models/__init__.py` 显式 import，否则 Alembic autogenerate 与 `Base.metadata` 漏表。当前已注册：`User`、`LoginLog`、`Alert`、`AuditLog`。
2. 新路由文件需在 `backend/app/main.py` 手动 `import` 并 `app.include_router(..., prefix=settings.API_V1_PREFIX, tags=[...])` —— 没有自动扫描。
3. Schema 的 `response_model` 类需 `model_config = ConfigDict(from_attributes=True)`，否则从 ORM 反序列化报错。
4. 建表用 `alembic upgrade head`，不要用 `Base.metadata.create_all()`。`alembic/env.py` 会从 `settings.DATABASE_URL` 覆盖连接串，但 `alembic.ini` 仍保留了一份静态 `sqlalchemy.url` 作为回退。
5. 创建默认管理员：`cd backend && python scripts/seed.py`（账号 `admin` / `admin123`，并置 `must_change_password=True` —— 首次登录必须改密）。

## 枚举词汇表（已由 `core/vocab.py` + Pydantic `Literal` 收敛）

写入接口会校验非法取值（422），但**数据库列仍是裸字符串、无 CHECK 约束**，绕过 API 直接写库仍可能写错，改动时按表核对：

| 字段 | 取值 |
|---|---|
| `Alert.alert_type` | `frequency`、`device` |
| `Alert.severity` | `low`、`medium`、`high` |
| `Alert.status` | `pending`、`acknowledged`、`resolved`；`AlertUpdate` 用 `Literal` 校验，从 resolved 回退会清空 `resolved_at` |
| `LoginLog.login_status` | **规范值 `success` / `failure`**（词表见 `core/vocab.py`）；入库即校验，`failed`/`fail` 自动归一化为 `failure` |
| `User.role` | 默认 `admin` |

告警去重视 `status`：`resolved` / `acknowledged` 不阻塞新告警，只有 `pending` 会。

## 常用命令

### 后端（工作目录 `backend/`）

```bash
uvicorn app.main:app --reload --port 8001   # 开发服务器
alembic upgrade head                        # 应用迁移
alembic revision --autogenerate -m "描述"    # 生成迁移
python scripts/seed.py                      # 创建默认管理员（admin / admin123）
python scripts/seed_logs.py                 # 只灌登录日志测试数据
python scripts/generate_mock_data.py        # 造日志+告警样本（会先清空 alerts/login_logs 两表）
python scripts/detection_smoke.py           # 免 Celery 的检测 + 去重冒烟
celery -A app.tasks worker --loglevel=info  # Celery Worker
celery -A app.tasks beat --loglevel=info    # 定时检测（每小时）
black .                                     # 格式化
```

`scripts/` 下脚本自身会 `sys.path.insert` 项目根，但 `pydantic-settings` 读 `.env` 依赖 **cwd 为 `backend/`**。Windows/PowerShell 下若报导入错误，先 `$env:PYTHONPATH="."` 再执行。

### 前端（工作目录 `frontend/`）

```bash
npm install
npm run dev        # 开发服务器 :5173
npm run build      # 生产构建 → dist/
npm run preview    # 预览生产构建
```

### Docker（项目根目录）

```bash
docker-compose up -d                 # 全部 6 个服务
docker-compose up -d mysql redis     # 只要基础设施（本地开发用这个，见下）
docker-compose down
```

## 测试约定

- 测试在 `backend/tests/`，`conftest.py` 提供 `engine`、`client`、`db` 三个 fixture。
- `engine` fixture 用**临时 SQLite**（自动创建 + 测试后清理），不依赖 Docker MySQL。
- Celery `delay()` 通过 `mock.patch` 跳过，测试环境无 Redis；Redis pub/sub 同样 `patch("app.tasks.detection.redis.from_url")`。
- 全部 **70** 个测试可离线运行（health 1 + security 2 + alert_stats 4 + detection 6 + integration 29 + contract 6 + config 8 + resilience 2 + governance 12）。Celery 投递由 `conftest.py` 的全局 autouse fixture 统一屏蔽，**无需 Redis**。

```bash
cd backend
pytest tests/ -v                                    # 全量
pytest tests/test_detection.py -v                   # 单文件
pytest tests/test_integration.py::test_xxx -v       # 单用例
```

## Lint / 格式化

- Black 配置在 `backend/pyproject.toml`：`line-length=100`（非默认 88），target py311，排除 `alembic/`。
- **`black` 与 `flake8` 均未列入 `requirements.txt`**，需手动 `pip install`。`flake8` 无配置文件，需显式 `flake8 app --max-line-length 100`。
- **前端没有可用的 lint 管线**：`package.json` 无 `lint` 脚本，devDependencies 无 eslint/prettier。`.eslintrc.cjs` 是 stub，对 `.vue` 无效。
- 唯一可信的后端格式化命令：`cd backend && black .`。

## 后端环境变量

- `pydantic-settings` 从 `.env`（相对 `backend/` 运行目录）加载，`case_sensitive=True` —— key 必须大写。
- `backend/.env` 已被 `.gitignore` 忽略；`backend/.env.example` 是模板。
- `backend/.env.example` 与 `config.py` 的 `ACCESS_TOKEN_EXPIRE_MINUTES` 已统一为 `1440`（24h）。
- **`API_KEY`** 默认 `"dev-api-key-change-in-production"`（`config.py`）。已在 `app/core/deps.py` `verify_api_key` 中实际用于 `X-API-Key` 头校验。覆盖需加大写 key 到 `backend/.env`。
- `SECRET_KEY` 与 `API_KEY` 为 dev 占位值，生产必须改；**启动期自检**会检测占位值：`ENVIRONMENT=production` 时直接拒绝启动，开发环境打印 WARNING（见 `core/config.py:assert_secure_config`）。
- `config.py` 默认 `DATABASE_URL` 端口已统一为 Docker/开发实际使用的 `8881`。
- 新增配置项：`ENVIRONMENT`（`development`/`production`）与 `BUSINESS_TIMEZONE`（默认 `Asia/Shanghai`，统计自然日与 Celery 调度共用）；`LOGIN_MAX_FAILURES`（默认 5）与 `LOGIN_FAILURE_WINDOW_SECONDS`（默认 900）控制登录限流。
- 邮件告警默认跳过（`app/tasks/email.py` 中 `is_email_configured()` 在 `EMAIL_USER` 为空或 host 含 `example` 时返回 False），不影响告警生成主流程。填真实 SMTP 凭据到 `.env` 即启用，无需改代码。
- **163 邮箱 SMTP 必须用端口 465 + SSL**（`SMTP_SSL`），587 + STARTTLS 实测连接失败。`.env.example` 默认已用 465。
- 根目录 `.env.example` 的 `DATABASE_URL` 端口已同步为 `8881`，两份模板保持一致。
- `frontend/.env` 可为空：开发时 Vite proxy 处理 `/api` 转发到 `localhost:8001`，无需 `VITE_API_BASE_URL`。
- **`GET /api/settings/email`** 可查看邮件配置状态（不需要 `.env` 即可判断）。
- **`POST /api/settings/email/test`** 发送测试邮件，快速诊断 SMTP 凭据问题。

## 易踩坑

- **时区（已统一，勿再混用 UTC 日界）**：数据库一律存 UTC naive；`GET /api/stats` 的「今日/趋势」按 `BUSINESS_TIMEZONE`（默认 `Asia/Shanghai`）自然日切分，Celery 使用同一时区。跨库日期折算在 `api/stats.py:_business_date_expr` 按方言处理（SQLite / MySQL），改这段要同时保证两种方言可用。
- **Vite proxy 顺序敏感**：`frontend/vite.config.js` 中 `/api/notifications` 必须排在 `/api` **之前**，且带 `ws: false` 与 `Connection: keep-alive`，否则 SSE 被普通代理规则吞掉，前端永远收不到实时告警。调代理配置时不要调换顺序。
- **`app/core/redis.py` 是死代码**：仅定义一个 `redis_client`，全仓无任何 import。实际 Redis 客户端在 `tasks/detection.py` 里用 `redis.from_url()` 自建。别把它当现成依赖来用。
- **`docker-compose up -d` 会拉起全部 6 个服务**，不只是 MySQL + Redis —— 会额外占用 8000 / 8882 端口。本地开发只需基础设施时用 `docker-compose up -d mysql redis`。
- **销毁类端点需要显式确认**：`DELETE /api/logs?confirm=true`、`DELETE /api/alerts?scope=all|processed&confirm=true`。缺 `confirm=true` 返回 **409**；执行的是**软删除**（写 `deleted_at`，从所有查询/统计中消失但数据保留）并写入 `audit_logs`。清空接口因此不再触发外键冲突。
- **`frontend/dist/` 已被 `.gitignore` 忽略，不在仓库里**（易误解为已提交产物）。前端 Docker 镜像在容器内从源码构建（`frontend/Dockerfile`：`COPY . .` → `npm run build`），与宿主机 `dist/` 无关。改前端后 8882 看不到改动时，重建镜像：`docker-compose up -d --build frontend`。
- **CORS 是 `allow_origins=["*"]` + `allow_credentials=True`**（`app/main.py`），仅适合开发，上线前需收敛。
- **Celery 任务不再吞异常**：`detect_anomaly_for_log` / `run_anomaly_detection` 会 `logger.exception` 留痕并 `self.retry` 有限重试；定时检测的 Redis 游标**在处理成功后才推进**（失败时保留原游标，下一轮重新覆盖该窗口，避免永久漏检）。

## `monitored-app/`（独立仿真应用，非主平台）

- 独立的 **Flask** 应用（非 FastAPI），运行在 **port 5000**，模拟被监控系统。
- 用途：向主平台 `POST /api/logs` 发送测试日志，也可通过 `/api/simulate` 生成异常样本。
- 启动：`cd monitored-app && pip install -r requirements.txt && python seed.py && python app.py`。
- 不依赖 Docker/MySQL/Redis，仅用于生成测试数据。数据库是本地 SQLite（`users.db`），与主平台技术栈无关，别按 FastAPI 那套改。

## 启动顺序

### Docker 一键部署

```bash
docker-compose up -d
```
访问 http://localhost:8882，管理员 admin / admin123。Migrations + seed 自动执行。

### 本地开发

```bash
docker-compose up -d mysql redis              # 1. 只要 MySQL + Redis（必需）
cd backend && pip install -r requirements.txt
alembic upgrade head                          # 2. 建表
python scripts/seed.py                        # 3. 创建管理员
uvicorn app.main:app --reload --port 8001     # 4. 后端
# 另开终端：
cd frontend && npm install && npm run dev     # 5. 前端 :5173
# 可选：
celery -A app.tasks worker --loglevel=info    # Celery Worker
celery -A app.tasks beat --loglevel=info      # 定时检测（每小时）
```

Celery 需 Redis（端口 8880）运行，否则 worker 启动失败；**但 Redis 不可用不会让上报失败**：`POST /api/logs` 仍返回 201（投递失败只记日志，由每小时 Beat 增量扫描兜底补检，见"架构与检测链路"）。

## 已知结构边界（当前规模不重构）

- **`core/` 职责集中** — `config / database / security / deps` 同放 `app/core/`。当前文件均小（5–69 行）、边界清晰，拆分成本高于收益。待 `core/` 显著膨胀后再拆。（`core/redis.py` 已废弃，不计入。）
- **schema 直接用于 API 层响应** — service 返回 ORM 对象，由 Pydantic `response_model` + `from_attributes=True` 直接序列化，无 DTO 转换层。当前 service 多为薄封装，引入 DTO 属过度抽象。

## 参考（避免重复读取）

- 详细设计、数据流、字段定义：`docs/DESIGN.md`
- UI 规范：`docs/UI.md`
- 技术栈、命令、JWT 流程、架构与全量技术文档：`docs/tech/README.md`
- 各周实现计划与历史决策依据：`docs/superpowers/plans/`、`docs/specs/`
