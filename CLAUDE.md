# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**校园账号异常登录监测与告警平台** — 安全审计与日志分析系统，检测校园账号异常登录并发送告警。

- **类型**：学术项目/毕业设计 | **当前阶段**：实习版第1周（共8周）
- **详细设计**：[docs/DESIGN.md](docs/DESIGN.md)（含完整数据模型、周计划、代码模式）

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | **MySQL**（强制，非 PostgreSQL） |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vue Router |
| 分析 | Pandas + NumPy + Scikit-learn |

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/          # 路由层 - 每个功能一个文件
│   │   ├── core/         # 配置、数据库/Redis 连接
│   │   ├── models/       # SQLAlchemy 模型（User, LoginLog, Alert）
│   │   ├── schemas/      # Pydantic 请求/响应模式（当前为空）
│   │   ├── services/     # 业务逻辑（当前为空）
│   │   ├── tasks/        # Celery 异步任务（当前为空）
│   │   ├── utils/        # 工具函数（当前为空）
│   │   └── main.py       # FastAPI 入口 - 只做组装，不写业务逻辑
│   ├── alembic/          # 数据库迁移（env.py 已导入所有模型）
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/          # Axios 客户端（已配置 JWT 拦截器和 401 跳转）
│   │   ├── router/       # Vue Router（Dashboard + Login 两条路由）
│   │   ├── views/        # 页面组件（Dashboard.vue, Login.vue）
│   │   └── main.js       # Vue 入口（已集成 Pinia + Element Plus 中文包）
│   └── Dockerfile
├── docs/DESIGN.md        # 完整设计文档
└── docker-compose.yml    # MySQL 8.0 + Redis 7
```

## 数据流

```
请求 → api/xxx.py (路由) → schemas/xxx.py (校验) → services/xxx.py (业务) → models/xxx.py (ORM) → MySQL
                                                                          ↕ Celery 异步
                                                                   tasks/xxx.py (邮件/检测)
```

## JWT 认证流程

```
前端 localStorage 存 token → Axios 拦截器自动附带 Bearer 头 → 后端验证 → 401 时前端自动跳转 /login
```

- `frontend/src/api/index.js` 已配置请求拦截器（附 token）和响应拦截器（401 清除 token 并跳转）
- `backend/app/core/config.py` 配置 JWT 参数（`SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ALGORITHM`）

## 添加新功能

### 后端 API 模块
1. 创建 `app/api/xxx.py`，定义 `router = APIRouter()`
2. 在 `app/main.py` 中 `app.include_router(router, prefix="/api", tags=["标签"])`

### 数据模型
1. 在 `app/models/` 下创建文件，继承 `Base`
2. 在 `alembic/env.py` 中 import 新模型
3. `alembic revision --autogenerate -m "描述" && alembic upgrade head`

## 常用命令

### 后端（backend/ 目录内）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # 启动开发服务器
alembic upgrade head                                        # 应用迁移
alembic revision --autogenerate -m "描述"                   # 生成迁移
pytest [-v] [tests/test_file.py]                            # 运行测试
black app/ tests/ && flake8 app/ tests/                     # 格式化+检查
celery -A app.tasks worker --loglevel=info                  # 启动 Celery
```

### 前端（frontend/ 目录内）
```bash
npm run dev     # 启动（端口 5173，已配置 /api → localhost:8000 代理）
npm run build   # 构建生产版本
npm run lint    # ESLint 检查
```

### Docker（项目根目录）
```bash
docker-compose up -d                          # 启动 MySQL + Redis
docker-compose logs -f backend                # 查看后端日志
docker-compose down                           # 停止
```

## 约束（源自 .harness/）

**每次任务必须**：
1. 在 `.harness/changes/YYYY-MM-DD-task-name/task.md` 创建任务文件，写明目标和验收标准
2. 代码修改后验证，完成后在 task.md 填写验证结果
3. 文档与代码同步更新，放入同一变更文件夹
4. 严禁修改 `.harness` 目录结构（仅可读写其下内容）

**技术约束**：
- 数据库：MySQL（强制） | 认证：JWT + RBAC（user/admin） | 异步：Celery + Redis
- 后端：Black + Flake8 | 前端：ESLint + Prettier
- API 文档：FastAPI 自动生成，访问 `/docs`

## 细节

- **开发代理**：`vite.config.js` 已将 `/api` 代理到 `localhost:8000`，前端开发时不需处理 CORS
- **数据库迁移**：`alembic.ini` 中的 `sqlalchemy.url` 使用独立凭据（`campus_user`/`campus123`，同 Docker compose），有别于 `.env` 中的 `DATABASE_URL`（`root`/`password`）
- **数据库自动建表**：`backend/app/main.py` 启动时调用 `Base.metadata.create_all(bind=engine)`（开发阶段免手动迁移）；正式上线依赖 Alembic
- **数据库连接模式**：backend 通过 `get_db()` 依赖注入提供 Session（`backend/app/core/database.py` 第 11-16 行）
- **Docker 国内环境**：首次启动 MySQL/Redis 容器时需注意镜像源配置
- **Env 文件**：`backend/.env` 已配置默认值，部署时需修改 `SECRET_KEY`
