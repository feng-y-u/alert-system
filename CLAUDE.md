# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**校园账号异常登录监测与告警平台** — 安全审计与日志分析系统。监控/运维类平台，不是面向师生的业务系统。

> 数据流：校园系统（被监控）→ 发送登录日志 → 本平台 → 检测异常 → 告警 → 管理员处理

- **类型**：学术项目/毕业设计
- **详细设计**：[docs/DESIGN.md](docs/DESIGN.md)
- **当前进展**：第2周（管理员认证）

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | **MySQL**（强制，非 PostgreSQL） |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vue Router |
| 分析 | Pandas + NumPy |
| 约束 | 后端 Black + Flake8，前端 ESLint + Prettier，API 文档 `/docs` |

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

## 数据流

```
请求 → api/xxx.py → schemas/xxx.py（校验）→ services/xxx.py（业务）→ models/xxx.py（ORM）→ MySQL
                                                                 ↕ Celery 异步
                                                          tasks/xxx.py（邮件/检测）
```

## API 路由

所有路由挂载在 `prefix="/api"` 下（`settings.API_V1_PREFIX`），非 `/api/v1`。新增路由：

```python
# app/api/xxx.py
from fastapi import APIRouter
router = APIRouter()

# app/main.py
from app.api.xxx import router as xxx_router
app.include_router(xxx_router, prefix=settings.API_V1_PREFIX, tags=["标签"])
```

## 数据库

- **连接**：`get_db()` 依赖注入提供 `Session`（[app/core/database.py](backend/app/core/database.py)）
- **ORM 基类**：`Base = declarative_base()`，所有模型继承 `Base`
- **模型注册**：新模型必须在 [app/models/__init__.py](backend/app/models/__init__.py) 中 import
- **迁移**：必须通过 `alembic upgrade head` 建表，不使用 `create_all`
- **配置**：`pydantic-settings` 从 `.env` 加载（[app/core/config.py](backend/app/core/config.py)）
- **关键配置**：`DATABASE_URL`（MySQL）、`SECRET_KEY`（生产环境必须修改）、`ACCESS_TOKEN_EXPIRE_MINUTES`（默认24h）

## Schema 模式

每个功能对应一个 schema 文件，定义 Pydantic 请求/响应模型，`response_model` 需配置 `from_attributes=True`。

## JWT 认证流程

```
登录成功 → 后端返回 JWT → 前端存入 localStorage
后续请求 → Axios 拦截器自动附加 Bearer 头
后端受保护路由 → Depends(get_current_active_user)
Token 过期/无效 → 后端返回 401 → 前端清除 token 并跳转 /login
```

关键文件：[security.py](backend/app/core/security.py)（创建/解码）、[deps.py](backend/app/core/deps.py)（依赖注入）、[auth.py](backend/app/api/auth.py)（路由）

## 测试

```bash
pytest [-v] [tests/test_file.py] [-k test_name]
```

使用 pytest + httpx（TestClient），测试文件放在 `tests/`，`conftest.py` 提供 `client` fixture。

## 常用命令

### 后端（`backend/` 目录）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # 开发服务器
alembic upgrade head                                        # 应用迁移
alembic revision --autogenerate -m "描述"                    # 生成迁移
pytest                                                      # 测试
celery -A app.tasks worker --loglevel=info                   # 异步任务
black . && flake8                                           # 格式化 + 检查
```

### 前端（`frontend/` 目录）
```bash
npm run dev      # 启动（端口 5173）
npm run build    # 构建
npm run lint     # ESLint 检查 + 修复
```

### Docker（项目根目录）
```bash
docker-compose up -d    # 启动 MySQL 8.0 + Redis 7
docker-compose down     # 停止
```

## 环境变量

```bash
# backend/.env
DATABASE_URL=mysql+pymysql://campus_user:campus123@localhost:3306/campus_monitor
REDIS_URL=redis://localhost:6479/0
SECRET_KEY=dev-secret-key-change-in-production

# frontend/.env（Vite 环境变量必须以 VITE_ 开头）
VITE_API_BASE_URL=http://localhost:8000
```

## 已实现的模块

| 模块 | 文件 | 状态 |
|---|---|---|
| 健康检查 | [api/health.py](backend/app/api/health.py) | ✅ |
| 用户认证（JWT） | auth.py + security.py + deps.py | ✅ |
| 用户模型 | [models/user.py](backend/app/models/user.py) | ✅ |
| 登录日志模型 | [models/login_log.py](backend/app/models/login_log.py) | ✅ |
| 告警模型 | [models/alert.py](backend/app/models/alert.py) | ✅ |
| 前端路由 | [router/index.js](frontend/src/router/index.js) | ✅ |
| Axios 客户端 | [api/index.js](frontend/src/api/index.js) | ✅ |
| Pinia 认证状态 | [stores/auth.js](frontend/src/stores/auth.js) | ✅ |
| Dashboard 页 | [views/Dashboard.vue](frontend/src/views/Dashboard.vue) | ⚠️ 骨架 |
| Login 页 | [views/Login.vue](frontend/src/views/Login.vue) | ✅ |
| Celery 任务 | [tasks/email.py](backend/app/tasks/email.py) + [detection.py](backend/app/tasks/detection.py) | ⚠️ 占位 |
| 单元测试 | [tests/test_security.py](backend/tests/test_security.py) | ✅ |