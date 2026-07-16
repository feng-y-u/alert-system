# AGENTS.md

OpenCode 专用速查。与 `CLAUDE.md` 互补：本文件只记录**易踩坑、文档/config 不一致或需要交叉多处才能推断**的事实。

## 关键路径与端口

- **Redis 主机端口是 8880**（非 6379）。`docker-compose.yml` 把容器 6379 映射到主机 8880。
- **API 前缀是 `/api`，不是 `/api/v1`**。配置变量名 `API_V1_PREFIX` 但值是 `"/api"`。新增路由统一用 `prefix=settings.API_V1_PREFIX`。
- 后端 dev port **8001**，前端 Vite port **5173**，Vite 代理 `/api → http://localhost:8001`。
- Docker Compose 主机端口：MySQL `8881`、Redis `8880`、Backend `8000`、Frontend `8882`（→容器 80）。
- **Docker 中 migration + seed 自动执行**（`docker-entrypoint.sh` 启动前先跑 `alembic upgrade head` + `python scripts/seed.py`）。
- 没有 CI、pre-commit、`opencode.json`。

## 添加新功能的固定步骤（易漏）

1. 新模型必须在 `backend/app/models/__init__.py` 显式 import，否则 Alembic autogenerate 与 `Base.metadata` 漏表。当前已注册：`User`、`LoginLog`、`Alert`。
2. 新路由文件需在 `backend/app/main.py` 手动 `import` 并 `app.include_router(..., prefix=settings.API_V1_PREFIX, tags=[...])` —— 没有自动扫描。
3. Schema 的 `response_model` 类需 `model_config = ConfigDict(from_attributes=True)`，否则从 ORM 反序列化报错。
4. 建表用 `alembic upgrade head`，不要用 `Base.metadata.create_all()`。`alembic/env.py` 会从 `settings.DATABASE_URL` 覆盖连接串，但 `alembic.ini` 仍保留了一份静态 `sqlalchemy.url` 作为回退。
5. 创建默认管理员：`cd backend && python scripts/seed.py`（账号 `admin` / `admin123`）。

## 测试约定

- 测试在 `backend/tests/`，`conftest.py` 提供 `engine`、`client`、`db` 三个 fixture。
- `engine` fixture 用**临时 SQLite**（自动创建 + 测试后清理），不依赖 Docker MySQL。
- Celery `delay()` 通过 `mock.patch` 跳过，测试环境无 Redis。
- 全部 42 个测试可离线运行。现有文件：`test_health.py`、`test_security.py`、`test_detection.py`、`test_alert_stats.py`、`test_integration.py`。
- 工作目录 `backend/`，`cd backend && pytest tests/test_xxx.py -v`。

## Lint / 格式化

- Black 配置在 `backend/pyproject.toml`：`line-length=100`（非默认 88），target py311，排除 `alembic/`。
- **`black` 与 `flake8` 均未列入 `requirements.txt`**，需手动 `pip install`。`flake8` 无配置文件，需显式 `flake8 app --max-line-length 100`。
- **前端没有可用的 lint 管线**：`package.json` 无 `lint` 脚本，devDependencies 无 eslint/prettier。`.eslintrc.cjs` 是 stub，对 `.vue` 无效。
- 唯一可信的后端格式化命令：`cd backend && black .`。

## 后端环境变量

- `pydantic-settings` 从 `.env`（相对 `backend/` 运行目录）加载，`case_sensitive=True` —— key 必须大写。
- `backend/.env` 已被 `.gitignore` 忽略；`backend/.env.example` 是模板。
- `backend/.env.example` 写的 `ACCESS_TOKEN_EXPIRE_MINUTES=30`，而 `config.py` 默认是 `1440`（24h）。复制模板会导致有效期缩短。
- **`API_KEY`** 默认 `"dev-api-key-change-in-production"`（`config.py`）。已在 `app/core/deps.py` `verify_api_key` 中实际用于 `X-API-Key` 头校验。覆盖需加大写 key 到 `backend/.env`。
- `SECRET_KEY` 与 `API_KEY` 为 dev 占位值，生产必须改。
- `config.py` 默认 `DATABASE_URL` 是端口 3306，但实际 Docker 与 `.env.example` 用的是 8881 —— 新建 `.env` 需确认端口。
- 邮件告警默认跳过（`app/tasks/email.py` 中 `is_email_configured()` 在 `EMAIL_USER` 为空或 host 含 `example` 时返回 False），不影响告警生成主流程。填真实 SMTP 凭据到 `.env` 即启用，无需改代码。
- **163 邮箱 SMTP 必须用端口 465 + SSL**（`SMTP_SSL`），587 + STARTTLS 实测连接失败。`.env.example` 默认已用 465。
- **根目录 `.env.example` 端口过时**：`DATABASE_URL` 写了 `3306`（应为 `8881`）。始终以 `backend/.env.example` 为准。
- `frontend/.env` 可为空：开发时 Vite proxy 处理 `/api` 转发到 `localhost:8001`，无需 `VITE_API_BASE_URL`。
- **`GET /api/settings/email`** 可查看邮件配置状态（不需要 `.env` 即可判断）。
- **`POST /api/settings/email/test`** 发送测试邮件，快速诊断 SMTP 凭据问题。

## `monitored-app/`（独立仿真应用，非主平台）

- 独立的 **Flask** 应用（非 FastAPI），运行在 **port 5000**，模拟被监控系统。
- 用途：向主平台 `POST /api/logs` 发送测试日志，也可通过 `/api/simulate` 生成异常样本。
- 启动：`cd monitored-app && pip install -r requirements.txt && python seed.py && python app.py`。
- 不依赖 Docker/MySQL/Redis，仅用于生成测试数据。

## 启动顺序

### Docker 一键部署

```bash
docker-compose up -d
```
访问 http://localhost:8882，管理员 admin / admin123。Migrations + seed 自动执行。

### 本地开发

```bash
docker-compose up -d                     # 1. MySQL + Redis（必需）
cd backend && pip install -r requirements.txt
alembic upgrade head                     # 2. 建表
python scripts/seed.py                   # 3. 创建管理员
uvicorn app.main:app --reload --port 8001  # 4. 后端
# 另开终端：
cd frontend && npm install && npm run dev  # 5. 前端 :5173
# 可选：
celery -A app.tasks worker --loglevel=info   # Celery Worker
celery -A app.tasks beat --loglevel=info     # 定时检测（每小时）
```

Celery 需 Redis（端口 8880）运行，否则 worker 启动失败。

## 已知结构边界（当前规模不重构）

- **`core/` 职责集中** — `config / database / security / deps / redis` 五类同放 `app/core/`。当前文件均小（5–69 行）、边界清晰，拆分成本高于收益。待 `core/` 显著膨胀后再拆。
- **schema 直接用于 API 层响应** — service 返回 ORM 对象，由 Pydantic `response_model` + `from_attributes=True` 直接序列化，无 DTO 转换层。当前 service 多为薄封装，引入 DTO 属过度抽象。

## 参考（避免重复读取）

- 详细设计、数据流、字段定义：`docs/DESIGN.md`
- UI 规范：`docs/UI.md`
- 技术栈、命令、JWT 流程：`CLAUDE.md`（本文件与 `CLAUDE.md` 冲突时以本文件为准 —— 已验证代码）
