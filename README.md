# 校园账号异常登录监测与告警平台

安全审计与日志分析系统，用于监测校园系统的登录行为，检测异常登录并发送告警。

> **定位**：监控/运维类平台。管理员登录后监控校园系统的登录日志，发现异常时处理告警。
> 被监控的师生**不是**本平台的用户，也不登录本平台。

```
校园系统（被监控）──POST /api/logs──▶ 本平台 ──检测异常──▶ 生成告警 ──▶ 管理员处理
```

## 核心能力

| 能力 | 说明 |
|---|---|
| 日志采集 | 校园系统以 `X-API-Key` 上报登录日志；入库时统一时间与状态词表 |
| 异常检测 | **频率异常**（5 分钟内同一账号登录 ≥10 次）与**设备异常**（1 小时内 ≥3 个不同 IP+UA 组合） |
| 告警去重 | 24 小时内同一用户同类型只保留一条待处理告警；并发场景由数据库唯一索引保证 |
| 实时推送 | 告警经 Redis pub/sub → SSE 推送至管理端，含未读徽标与断线重连 |
| 邮件通知 | 异步发送给全部启用中的管理员；未配置 SMTP 自动跳过 |
| 告警闭环 | `pending → acknowledged → resolved` 状态机，处理时间留痕 |
| 审计留痕 | 平台自身关键操作写入 `audit_logs`（登录、改密、创建管理员、清空、状态变更） |
| 数据可视化 | 仪表盘：今日登录 / 待处理告警 / 活跃用户 + 登录趋势 + 告警趋势 + 类型/级别分布 |

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | MySQL 8.0 |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vue Router + Vite |
| 认证 | JWT（HS256）+ bcrypt；日志上报使用 `X-API-Key` |
| 部署 | Docker Compose（6 服务）+ Nginx |

## 快速开始

### Docker 一键部署（推荐）

```bash
docker-compose up -d
```

自动启动 MySQL、Redis、后端、前端、Celery Worker、Celery Beat 六个服务。

| 服务 | 端口 | 说明 |
|---|---|---|
| 前端 | `8882` | Nginx 托管静态文件 + 反向代理（容器内为 80） |
| 后端 | `8000` | FastAPI API 服务 |
| MySQL | `8881` | 数据库 |
| Redis | `8880` | 缓存 + Celery Broker |
| Celery Worker | — | 消费检测与邮件任务 |
| Celery Beat | — | 每小时增量补检 |

首次启动后自动创建管理员账号：`admin` / `admin123`。
该口令是公开的示例值，**首次登录必须先修改密码**（前端会跳转到改密页；后端对其它接口一律 403）。

### 本地开发

#### 1. 启动基础服务

```bash
docker-compose up -d mysql redis    # 只起 MySQL 8.0 + Redis 7（本地开发用）
```

> ⚠️ 不要用 `docker-compose up -d`（会拉起全部 6 个服务并额外占用 8000 / 8882 端口）。

环境要求：Python 3.11+（Docker 镜像使用 3.12）、Node 18+（Docker 镜像使用 20）、Docker。

#### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head          # 应用数据库迁移
python scripts/seed.py        # 创建默认管理员（admin / admin123）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

API 文档：http://localhost:8001/docs

#### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

若后端跑在 Docker（8000 端口）而非本地 8001，用环境变量覆盖代理目标，无需改文件：

```bash
VITE_DEV_PROXY_TARGET=http://localhost:8000 npm run dev
```

#### 4. Celery 异步任务（可选，需 Redis 在 8880）

```bash
cd backend
celery -A app.tasks worker --loglevel=info     # Worker
celery -A app.tasks beat --loglevel=info       # 定时调度
```

> Redis 不可用**不会让日志上报失败**：`POST /api/logs` 仍返回 201（日志已落库），由每小时 Beat 的增量扫描兜底补检。

#### 5. 仿真上报端（可选）

`monitored-app/` 是一个独立的 Flask 应用，模拟被监控的校园系统，用于生成测试数据：

```bash
cd monitored-app
pip install -r requirements.txt
python seed.py
python app.py                                  # http://localhost:5000
```

它可向主平台发送登录日志，也可通过 `POST /api/simulate` 一键生成频率异常 / 设备异常样本。
该应用技术栈与主平台无关，仅供本地造数使用，**请勿对外部署**。

## 异常检测规则

检测实现位于 `backend/app/services/detection.py`，两个入口复用同一套规则：

- **实时**：`POST /api/logs` 落库后投递 `detect_anomaly_for_log(log_id)`，以该条日志的 `login_time` 作为窗口终点；
- **定时**：Celery Beat 每小时执行 `run_anomaly_detection()`，增量扫描上次检测后新增日志所属的用户（游标存 Redis 键 `anomaly_detection:last_check_time`）。

| 规则 | 类型值 | 触发条件 | 严重级别 | 告警文案 |
|---|---|---|---|---|
| 频率异常 | `frequency` | 5 分钟内同一用户名登录 **≥10 次** | 10–30 次 → `medium`<br>>30 次 → `high` | `用户 X 在5分钟内登录 N 次，可能存在异常` / `…疑似暴力破解攻击` |
| 设备异常 | `device` | 1 小时内同一用户名出现 **≥3 个**不同 `(user_agent, ip_address)` 组合 | 3~4 个 → `medium`<br>≥5 个 → `high` | `用户 X 在1小时内使用 N 个不同设备登录` / `…使用 N 个不同设备登录，疑似账号共享或被盗` |

**去重**：应用层检查 24 小时内是否存在同 `username` + 同 `alert_type` 的 `pending` 告警；数据库层由生成列 `pending_dedup_key` + 唯一索引 `uq_alerts_pending_dedup` 保证并发下不重复。

> 📌 需要准确理解的两点：
> 1. 频率规则统计的是**登录次数，不区分成功与失败**（源码中筛选条件不含 `login_status`）。
> 2. 「设备」在本项目中**精确等于 `(user_agent, ip_address)` 二元组的去重计数**，不是设备指纹，不做 UA 解析。
>
> 另外，词表虽定义了 `low` 级别，但**当前检测逻辑不会产生 `low` 告警**，实际只有 `medium` 与 `high`。

## 环境变量

复制模板文件并修改：

```bash
cp backend/.env.example backend/.env
```

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DATABASE_URL` | MySQL 连接地址 | `mysql+pymysql://campus_user:campus123@localhost:8881/campus_monitor` |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:8880/0` |
| `SECRET_KEY` | JWT 签名密钥（**生产必须替换**） | 源码默认 `your-secret-key-change-in-production`；模板为 `change-me-to-a-random-secret` |
| `API_KEY` | 日志写入 `X-API-Key` 校验值（**生产必须替换**） | `dev-api-key-change-in-production` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | `1440`（24 小时） |
| `ENVIRONMENT` | `development` / `production`；production 下使用占位密钥会**拒绝启动** | `development` |
| `BUSINESS_TIMEZONE` | 统计自然日与 Celery 调度共用时区（数据库始终存 UTC） | `Asia/Shanghai` |
| `LOGIN_MAX_FAILURES` | 同一「用户名 + IP」窗口内最多失败次数 | `5` |
| `LOGIN_FAILURE_WINDOW_SECONDS` | 登录失败限流窗口（秒） | `900` |
| `EMAIL_HOST` / `EMAIL_PORT` | SMTP 服务器与端口（**代码使用 `SMTP_SSL`，须配 SSL 端口**） | `smtp.example.com` / `465` |
| `EMAIL_USER` / `EMAIL_PASSWORD` | SMTP 账号与授权码；`EMAIL_USER` 为空即视为未配置，邮件自动跳过 | 空 |
| `ALERT_EMAIL_FROM` | 告警邮件发件人 | `campus-monitor@localhost` |
| `VITE_API_BASE_URL` | 前端 API 基址；开发经 Vite 代理时**无需设置** | 空 |
| `VITE_DEV_PROXY_TARGET` | Vite 开发代理目标 | `http://localhost:8001` |

> `pydantic-settings` 从**相对运行目录**的 `.env` 读取，且 `case_sensitive=True` —— key 必须大写，且需在 `backend/` 目录下启动进程。

## API 一览

前缀统一为 `/api`（**不是** `/api/v1`）。交互式文档见 `/docs`。

| 方法 | 路径 | 功能 | 鉴权 |
|---|---|---|---|
| GET | `/api/health` | 健康检查 | 无 |
| POST | `/api/auth/login` | 管理员登录（含失败限流，超限返回 429） | 无 |
| POST | `/api/auth/change-password` | 修改自己的密码（初始口令场景唯一可用的写接口） | Bearer JWT |
| POST | `/api/auth/register` | 创建新管理员 | Bearer JWT |
| GET | `/api/auth/me` | 当前登录用户信息 | Bearer JWT |
| POST | `/api/logs` | 接收登录日志（校园系统调用） | `X-API-Key` |
| GET | `/api/logs` | 查询日志（用户名模糊 / IP / 状态 / 时间范围 / 分页） | Bearer JWT |
| DELETE | `/api/logs` | 清空日志（**软删除**，需 `confirm=true`） | Bearer JWT |
| GET | `/api/alerts` | 告警列表（按状态 / 级别 / 用户名筛选） | Bearer JWT |
| GET | `/api/alerts/{id}` | 告警详情 | Bearer JWT |
| PUT | `/api/alerts/{id}` | 变更告警状态（非法转换返回 409） | Bearer JWT |
| DELETE | `/api/alerts` | 清空告警（软删除，`scope=all\|processed` 且需 `confirm=true`） | Bearer JWT |
| GET | `/api/stats` | 仪表盘统计（`days` 1–365） | Bearer JWT |
| GET | `/api/stats/alerts` | 告警趋势 / 类型分布 / 级别分布 | Bearer JWT |
| GET | `/api/notifications/stream` | SSE 实时告警流（token 走 query 参数） | `?token=<jwt>` |
| GET | `/api/settings/email` | 查看邮件配置状态（不返回密码） | Bearer JWT |
| POST | `/api/settings/email/test` | 发送测试邮件 | Bearer JWT |
| GET | `/api/audit-logs` | 查询平台自身操作审计记录 | Bearer JWT |

> SSE 用 query 传 token 不是设计瑕疵：浏览器 `EventSource` 无法附加自定义请求头，因此绕开了统一的 Bearer 依赖。

## 测试

```bash
cd backend
python -m pytest tests/ -v
```

**共 119 个用例，无需 Redis 与 MySQL 即可运行**（使用临时 SQLite，Celery 投递由 `conftest.py` 的全局 fixture 统一屏蔽），实测约 30 秒跑完。

| 测试文件 | 用例数 | 覆盖内容 |
|---|---|---|
| `test_integration.py` | 30 | 认证 → 日志写入 → 检测 → 告警 API → 统计 全流程 |
| `test_bug_fixes.py` | 35 | 缺陷回归集（BUG-001~010：时区折算、LIKE 转义、参数校验 422、未来时间拒绝等） |
| `test_governance.py` | 14 | 软删除 / 审计日志 / 确认参数 / 登录限流 / 初始密码强制修改 / 告警状态机 |
| `test_detection.py` | 13 | 频率与设备检测各级别（设备 3~4 个 → medium、≥5 个 → high）、去重语义、**双线程并发去重** |
| `test_config.py` | 8 | 占位密钥检测、启动自检、业务时区换算、配置摘要脱敏 |
| `test_contract.py` | 6 | 词表契约（`login_status` 归一化、告警状态校验、SSE 鉴权） |
| `test_alert_stats.py` | 4 | `/api/stats/alerts` 鉴权与趋势长度 |
| `test_stats_consistency.py` | 4 | 仪表盘「待处理告警」与告警列表口径一致性 |
| `test_security.py` | 2 | 密码哈希 / JWT 签发与解码 |
| `test_resilience.py` | 2 | broker 不可用时上报接口仍返回 201 |
| `test_health.py` | 1 | 健康检查 |

> ⚠️ 前端暂无自动化测试；未配置覆盖率工具。

## 项目结构

```
backend/
├── app/
│   ├── api/             API 路由（health / auth / logs / alerts / stats /
│   │                    notifications / settings / audit）
│   ├── core/            配置 + 数据库 + 安全 + 依赖注入 + 限流 + 词表
│   ├── models/          SQLAlchemy ORM 模型（User / LoginLog / Alert / AuditLog）
│   ├── schemas/         Pydantic 模式
│   ├── services/        业务逻辑（auth / logs / detection / audit）
│   └── tasks/           Celery 异步任务（检测、邮件）
├── alembic/             数据库迁移（当前 head: 2026_09_18_alert_dedup_uq）
├── tests/               pytest 测试（119 个用例）
├── scripts/             seed.py / seed_logs.py / generate_mock_data.py /
│                        detection_smoke.py
├── docker-entrypoint.sh 容器启动入口（迁移 + seed + 启动）
├── Dockerfile
└── requirements.txt
frontend/
├── src/
│   ├── api/             Axios 客户端 + 拦截器
│   ├── composables/     可复用逻辑（取数状态机、分页查询、计数动画、在线检测）
│   ├── components/      Vue 组件（图表、通用、告警、日志）
│   ├── layouts/         布局组件
│   ├── router/          路由配置 + 登录 / 改密守卫
│   ├── stores/          Pinia 状态管理（认证、通知/SSE）
│   ├── utils/           图表配置、动效令牌、格式化
│   └── views/           页面视图（登录 / 改密 / 仪表盘 / 登录日志 / 告警列表 / 系统设置）
├── nginx.conf           生产环境 Nginx 配置（含 SSE 专用代理）
├── Dockerfile           多阶段构建（Node + Nginx）
└── package.json
monitored-app/           独立仿真上报应用（Flask，仅本地造数用）
docker-compose.yml       全栈编排
```

## 安全提示

- `backend/.env` **已被 `.gitignore` 忽略**，请勿提交或随归档材料分发；其中若填写了真实 SMTP 凭据，泄露后应立即在邮箱服务商处重置授权码。
- `SECRET_KEY` 与 `API_KEY` 的默认值是**公开占位值**。项目在启动时会做自检：`ENVIRONMENT=production` 时命中占位值将**拒绝启动**，开发环境仅打印警告。部署到任何可访问的环境前必须替换为强随机值。
- 数据库口令在 `docker-compose.yml`、`backend/.env.example` 等处仍为开发用弱口令，生产环境请一并替换。
- 当前 `CORSMiddleware` 配置为 `allow_origins=["*"]` + `allow_credentials=True`，**仅适合开发**，上线前需收敛为前端域名白名单。
- Nginx 配置未包含 TLS，生产环境需在外层终止 HTTPS。

## 相关文档

- 源码级技术文档（架构、API、数据库、检测机制、安全与性能分析）：[docs/项目源码级技术文档.md](docs/项目源码级技术文档.md)
- 详细设计：[docs/DESIGN.md](docs/DESIGN.md)
- UI 规范：[docs/UI.md](docs/UI.md)
- 技术专题文档（01～14 + 附录共 15 篇，另含索引）：[docs/tech/](docs/tech/README.md)
- 开发速查与易踩坑清单：[AGENTS.md](AGENTS.md)
