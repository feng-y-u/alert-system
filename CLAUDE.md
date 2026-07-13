# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**校园账号异常登录监测与告警平台** — 安全审计与日志分析系统。监控/运维类平台，不是面向师生的业务系统。

> 数据流：校园系统（被监控）→ 发送登录日志 → 本平台 → 检测异常 → 告警 → 管理员处理

- **类型**：学术项目/毕业设计
- **详细设计**：[docs/DESIGN.md](docs/DESIGN.md)
- **UI 规范**：[docs/UI.md](docs/UI.md)

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | **MySQL**（强制，非 PostgreSQL） |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vue Router |
| 分析 | Pandas + NumPy |
| 约束 | 后端 Black + Flake8，前端 ESLint + Prettier，API 文档 `/docs` |

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
pytest                              # 运行所有测试
pytest -v                          # 详细输出
pytest tests/test_security.py      # 运行单个测试文件
pytest -k test_name                # 运行匹配名称的测试
```

使用 pytest + httpx（TestClient），测试文件放在 `tests/`，`conftest.py` 提供 `client` fixture。

## 常用命令

### 后端（`backend/` 目录）
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001   # 开发服务器
alembic upgrade head                                        # 应用迁移
alembic revision --autogenerate -m "描述"                    # 生成迁移
pytest                                                      # 运行测试
pytest -v                                                   # 详细测试输出
pytest tests/test_file.py -k test_func                      # 单测试/单函数
celery -A app.tasks worker --loglevel=info                   # 启动 Celery 工作进程
celery -A app.tasks beat --loglevel=info                     # 启动 Celery 调度器（定时任务）
python scripts/seed.py                                       # 创建默认管理员（admin / admin123）
black . && flake8                                           # 格式化 + 检查
```

### 前端（`frontend/` 目录）
```bash
npm run dev          # 启动开发服务器（端口 5173）
npm run build        # 生产构建（输出到 dist/）
npm run preview      # 预览生产构建
npm run lint         # ESLint 检查（package.json 中未配置修复）
```

前端使用 Vite 构建工具，Element Plus 组件库，Pinia 状态管理。

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
VITE_API_BASE_URL=http://localhost:8001
```

## 开发计划

| 周次 | 内容 | 状态 |
|------|------|------|
| 第1周 | 项目搭建：FastAPI框架 + MySQL/Redis + 基础模型 + Vue 3 + Docker | ✅ |
| 第2周 | 管理员认证：登录/注册 JWT API + seed 脚本 + 前端登录页 + 路由守卫 | ✅ |
| 第3周 | 登录日志管理：接收/查询 API + 模拟数据脚本 | ✅ |
| 第4周 | 异常检测：频率异常 + 设备异常 + Pandas 分析 | ✅ |
| 第5周 | 告警系统：生成/查询 API + 邮件通知 | ⏳ 待开始 |
| 第6周 | 前端页面联调：日志列表 + 告警列表 + ECharts 图表 | ❌ |
| 第7周 | 功能完善：实时通知 + 优化 + 错误处理 | ❌ |
| 第8周 | 测试与部署：集成测试 + Docker 部署 + 文档 | ❌ |

详细设计见 [docs/DESIGN.md](docs/DESIGN.md)，UI 规范见 [docs/UI.md](docs/UI.md)。