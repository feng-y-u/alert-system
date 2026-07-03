# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**校园账号异常登录监测与告警平台** — 安全审计与日志分析系统，用于监测校园系统的登录行为，检测异常登录并发送告警。

> **定位**：这是一个监控/运维类平台，不是面向师生的业务系统。管理员登录后监控校园系统的登录日志，发现异常时处理告警。
>
> **数据流**：校园系统（被监控）→ 发送登录日志 → 本平台 → 检测异常 → 告警 → 管理员处理

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

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/               # API 路由（每个功能一个文件）
│   │   ├── core/              # 配置 + 数据库连接
│   │   ├── models/            # SQLAlchemy ORM 模型
│   │   ├── schemas/           # Pydantic 请求/响应模式
│   │   ├── services/          # 业务逻辑
│   │   ├── tasks/             # Celery 异步任务
│   │   └── utils/             # 工具函数
│   ├── alembic/               # 数据库迁移
│   ├── tests/                 # pytest 测试
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── api/               # Axios 客户端
│   │   ├── components/        # Vue 组件
│   │   ├── layouts/           # 布局组件
│   │   ├── router/            # 路由配置
│   │   ├── stores/            # Pinia 状态管理
│   │   ├── views/             # 页面视图
│   │   └── utils/             # 工具函数
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml          # MySQL 8.0 + Redis 7
├── .env.example
└── CLAUDE.md
```

## 数据流

```
请求 → api/xxx.py (路由) → schemas/xxx.py (校验) → services/xxx.py (业务) → models/xxx.py (ORM) → MySQL
                                                                          ↕ Celery 异步
                                                                   tasks/xxx.py (邮件/检测)
```

## API 前缀与路由

后端所有路由挂载在 `prefix="/api"` 下（`settings.API_V1_PREFIX`），而非 `/api/v1`。新增路由时：

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
- **模型注册**：新模型必须在 [app/models/__init__.py](backend/app/models/__init__.py) 中 import，否则 Alembic `env.py` 无法发现
- **迁移**：
  ```bash
  alembic upgrade head                        # 应用迁移
  alembic revision --autogenerate -m "描述"    # 生成新迁移
  ```
  迁移文件会写入 `alembic/versions/`，需要 git add。
- **开发阶段**：不使用 `create_all`，必须通过 `alembic upgrade head` 建表

## Schema 模式

每个功能模块对应一个 schema 文件，定义请求体和响应体的 Pydantic 模型：

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True  # 支持 ORM 模式
```

## JWT 认证

```
前端 localStorage 存 token → Axios 拦截器自动附带 Bearer 头 → 后端验证 → 401 时前端自动跳转 /login
```

- **后端 JWT**：[app/core/auth.py](backend/app/core/auth.py)（暂未创建，集成 passlib + python-jose）
- **密码哈希**：`passlib[bcrypt]`
- **前端拦截器**：[frontend/src/api/index.js](frontend/src/api/index.js) 请求附 token、响应 401 清除 token 并跳转
- 前端路由无 auth guard，仅靠 401 跳转保护；后续可添加 `beforeEach` 导航守卫

## Celery 异步任务

Celery app 在 [app/tasks/__init__.py](backend/app/tasks/__init__.py) 中创建（暂未实现），按功能分散到模块：

```python
# app/tasks/email.py — 邮件发送
# app/tasks/detection.py — 异常检测
```

启动 worker：
```bash
celery -A app.tasks worker --loglevel=info
```

## 测试规范

用 pytest + httpx（AsyncClient）测试 API，测试文件放在 `tests/`：

```python
# tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
```

运行：
```bash
pytest                    # 全部测试
pytest -v                 # 详细输出
pytest tests/test_file.py # 单个文件
```

## 前端 Pinia Store

```javascript
// stores/auth.js
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({ token: null, user: null }),
  actions: {
    async login(username, password) { /* ... */ },
    logout() { this.token = null; this.user = null; },
  },
})
```

## 常用命令

### 后端（`backend/` 目录）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
alembic upgrade head
alembic revision --autogenerate -m "描述"
pytest [-v] [tests/test_file.py]
celery -A app.tasks worker --loglevel=info
black . && flake8        # 格式化 + lint
```

### 前端（`frontend/` 目录）
```bash
npm run dev      # 启动（端口 5173）
npm run build    # 构建生产版本
npm run lint     # ESLint 检查 + 修复
```

### Docker（项目根目录）
```bash
docker-compose up -d          # 启动 MySQL 8.0 + Redis 7
docker-compose logs -f        # 查看日志
docker-compose down           # 停止
```

## .harness 任务流程

**每次任务必须**：
1. 在 `.harness/changes/YYYY-MM-DD-task-name/task.md` 创建任务文件，写明目标和验收标准
2. 代码修改后验证，完成后在 task.md 填写验证结果
3. 文档与代码同步更新，放入同一变更文件夹
4. 严禁修改 `.harness` 目录结构（仅可读写其下内容）

## 技术约束

- 数据库：MySQL（强制）
- 认证：JWT + RBAC（user/admin 角色）
- 异步：Celery + Redis
- 后端格式化：Black + Flake8
- 前端格式化：ESLint + Prettier
- API 文档：FastAPI 自动生成，访问 `/docs`
- `backend/.env` 已配置默认值，部署时需修改 `SECRET_KEY`

## 已实现的模块

| 模块 | 文件 | 状态 |
|---|---|---|
| 健康检查 | [api/health.py](backend/app/api/health.py) | ✅ |
| 用户模型 | [models/user.py](backend/app/models/user.py) | ✅ |
| 登录日志模型 | [models/login_log.py](backend/app/models/login_log.py) | ✅ |
| 告警模型 | [models/alert.py](backend/app/models/alert.py) | ✅ |
| 前端路由 | [router/index.js](frontend/src/router/index.js) | ✅ |
| Axios 客户端 | [api/index.js](frontend/src/api/index.js) | ✅ |
| Dashboard 页 | [views/Dashboard.vue](frontend/src/views/Dashboard.vue) | ⚠️ 骨架 |
| Login 页 | [views/Login.vue](frontend/src/views/Login.vue) | ⚠️ 骨架 |