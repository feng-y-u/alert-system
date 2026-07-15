# AGENTS.md

OpenCode 专用速查。与 `CLAUDE.md` 互补：本文件只记录**易踩坑、文档/config 不一致或需要交叉多处才能推断**的事实。验证过的、能从 `CLAUDE.md`/`README.md` 直接看出的不重复。

## 关键路径与端口

- **Redis 主机端口是 8880**，不是 6379。`docker-compose.yml` 把容器 6379 映射到主机 8880。Docker 未启动时 Celery/缓存会失败。
- **API 前缀是 `/api`，不是 `/api/v1`** — 配置变量名叫 `API_V1_PREFIX` 但值是 `"/api"`。新增路由统一用 `prefix=settings.API_V1_PREFIX`。
- 后端 dev port **8001**，前端 Vite port **5173**，Vite 代理 `/api → http://localhost:8001`。
- Docker 生产部署：前端 port **80**（Nginx），后端容器内 port **8000**（映射到主机可自定义）。
- Docker Compose 服务（完整 6 服务已编排）：MySQL `localhost:8881`、Redis `localhost:8880`、Backend 8000、Frontend 80、Celery Worker、Celery Beat。
- 没有 CI、pre-commit、`opencode.json`。

## 添加新功能的强制步骤（易漏）

1. 新模型必须在 `backend/app/models/__init__.py` 显式 import，否则 Alembic autogenerate 与 `Base.metadata` 漏表。当前注册：`User`、`LoginLog`、`Alert`。
2. 新路由文件需在 `backend/app/main.py` 手动 `import` 并 `app.include_router(..., prefix=settings.API_V1_PREFIX, tags=[...])` —— 没有自动扫描。
3. Schema 的 `response_model` 类需 `model_config = ConfigDict(from_attributes=True)`，否则从 ORM 返回会报错。当前 `schemas/{user,alert,login_log}.py` 均是这种写法，照抄。
4. 建表用 `alembic upgrade head`，不要用 `Base.metadata.create_all()` 跑生产/开发库；autogenerate 用 `alembic revision --autogenerate -m "..."`。注意 `alembic.ini` 里硬编码了一份 `sqlalchemy.url`，与 `.env`/`config.py` 的 `DATABASE_URL` 是两处来源，改 DB 连接时两处都要改。Docker 部署时 `alembic/env.py` 会从 `settings.DATABASE_URL` 覆盖连接串。已更新 `env.py` 导入 `settings` 并使用 `config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)`。
5. 创建默认管理员：`cd backend && python scripts/seed.py`（账号 `admin` / `admin123`）。

## 测试约定

- 测试在 `backend/tests/`，`conftest.py` 提供 `engine`、`client`、`db` 三个 fixture。
- `engine` fixture 用**临时文件 SQLite**（自动创建 + 测试后清理），`client` 通过 `app.dependency_overrides[get_db]` 注入同一引擎，HTTP 请求与 `db` fixture 共享同一数据库。不需要 Docker MySQL。
- 跑单个测试：`pytest tests/test_xxx.py::TestClass::test_method -v`（工作目录为 `backend/`）。
- 当前测试文件：`test_health.py`、`test_security.py`、`test_detection.py`、`test_alert_stats.py`、`test_integration.py`（共 42 个测试）。
- 集成测试（`test_integration.py`）覆盖：认证→日志写入→异常检测→告警 API→统计→SSE 发布→去重。Celery `delay()` 通过 `mock.patch` 跳过（测试环境无 Redis）。
- 全部测试可离线运行，不依赖 MySQL/Redis。

## Lint / 格式化（注意 config 残缺，别盲信文档）

- Black 配置在 `backend/pyproject.toml`：`line-length = 100`（非默认 88），target py311，`alembic/` 已排除。
- **`black` 与 `flake8` 均未列入 `requirements.txt`**，使用前需手动 `pip install`。`flake8` 没有 `.flake8`/`setup.cfg`，默认 79 列会误报，需显式 `flake8 app --max-line-length 100`。
- **前端没有可用 lint 管线**：`package.json` 无 `lint` 脚本且 devDependencies 无 eslint/prettier。根目录有个 `.eslintrc.cjs` 是 stub —— 未配 `vue-eslint-parser`、未 `extends plugin:vue/*`，对 `.vue` 文件无效。不要据此推断前端经过 lint。
- 后端唯一可信的格式化命令：`cd backend && black .`。`CLAUDE.md` 与 README 中写的 "black . && flake8" 和 "npm run lint" 部分是不可执行命令，需先自行安装对应工具。

## 后端环境变量

- `pydantic-settings` 从 `.env`（相对 `backend/` 运行目录）加载，`case_sensitive=True` —— `.env` 里 key 必须是大写，否则不生效。
- `backend/.env` 已被 `.gitignore` 忽略，`backend/.env.example` 是其模板。注意 `backend/.env.example` 写了 `ACCESS_TOKEN_EXPIRE_MINUTES=30`，而 `config.py` 默认是 `1440`（=24h）。如果复制 `.env.example` → `.env`，token 有效期会从 24h 变成 30min。
- **`API_KEY` 不在 `backend/.env.example`**，默认值在 `config.py`：`"dev-api-key-change-in-production"`。`API_KEY` 已在 `app/core/deps.py` 实际用于 `X-API-Key` 头校验。要覆盖就把大写 key 加到 `backend/.env`。
- `SECRET_KEY` 与 `API_KEY` 为 dev 占位值，生产必须改。邮件告警走 `EMAIL_*` + `ALERT_EMAIL_FROM`（默认 `campus-monitor@localhost`）；`app/tasks/email.py` 的 `is_email_configured()` 在 `EMAIL_USER` 为空或 host 含 `example` 时返回 False，`send_alert_email` 任务优雅跳过（记 warning，不抛错），不影响告警生成主流程。告警在检测生成后通过 `send_alert_email.delay(alert_id)` 异步触发（见 `app/tasks/detection.py` 两处检测任务）。填真实 SMTP 凭据到 `backend/.env` 即启用，无需改代码。
- **163 邮箱 SMTP 需用端口 465 + SSL**（`email.py` 中 `smtplib.SMTP_SSL`），端口 587 + STARTTLS 实测连接失败。`.env` 默认端口已改为 465。

## 启动顺序

### Docker 一键部署（推荐）

```bash
docker-compose up -d    # MySQL + Redis + Backend + Frontend + Celery Worker + Celery Beat
```

访问 http://localhost，管理员 admin / admin123。首次自动 migration + seed。

### 本地开发

```bash
docker-compose up -d                     # 1. MySQL + Redis（必需）
cd backend && pip install -r requirements.txt
alembic upgrade head                     # 2. 建表
python scripts/seed.py                   # 3. 创建管理员
uvicorn app.main:app --reload --port 8001  # 4. 后端
# 另开终端，前端：
cd frontend && npm install && npm run dev  # 5. 前端 :5173
# 可选异步：celery -A app.tasks worker --loglevel=info
```

Celery 任务（邮件/检测）需 Redis（端口 8880）在跑，否则 worker 启动即报连不上 broker。Celery beat 调度器命令：`celery -A app.tasks beat --loglevel=info`。

## 已知边界（当前规模下不重构，扩展时再处理）

- **`core/` 职责集中** — `config.py / database.py / security.py / deps.py / redis.py` 五类职责同放 `app/core/`。当前文件均小（5–69 行）、边界清晰，拆成 `db/`、`security/`、`deps.py` 会牵动 `CLAUDE.md`、`AGENTS.md`、`DESIGN.md`、所有 `from app.core.x import` 与 alembic 引用，收益不抵成本。引入"告警规则配置界面"等扩展功能、`core/` 显著膨胀后再拆。
- **schema 直接用于 api 层响应** — service 返回 ORM 对象，由 Pydantic `response_model` + `from_attributes=True` 直接序列化，没有 service→DTO 转换层。当前 service 多为薄封装，引入 DTO 转换是 speculative abstraction。若出现 ORM 对象泄漏响应或 service 返回结构需稳定化的实际痛点了再加转换层。

## 参考（避免重复读取）

- 详细设计、数据流、字段定义：`docs/DESIGN.md`
- UI 规范：`docs/UI.md`
- 完整开发计划与命令：`CLAUDE.md`（本文件不重复其已被验证的内容；如本文件与 `CLAUDE.md` 冲突以本文件为准 —— 本文件已对照代码校验）