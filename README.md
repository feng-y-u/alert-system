# 校园账号异常登录监测与告警平台

安全审计与日志分析系统，用于监测校园系统的登录行为，检测异常登录并发送告警。

> **定位**：监控/运维类平台，不是面向师生的业务系统。管理员登录后监控校园系统的登录日志，发现异常时处理告警。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | MySQL 8.0 |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vue Router |
| 分析 | Pandas + NumPy |

## 快速开始

### 1. 启动基础服务

```bash
docker-compose up -d    # 启动 MySQL 8.0 + Redis 7
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head          # 应用数据库迁移
python scripts/seed.py        # 创建默认管理员（admin / admin123）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档访问 http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

## 项目结构

```
backend/
├── app/api/           # API 路由（每个功能一个文件）
├── app/core/          # 配置 + 数据库 + 安全 + 依赖注入
├── app/models/        # SQLAlchemy ORM 模型
├── app/schemas/       # Pydantic 请求/响应模式
├── app/services/      # 业务逻辑（当前为空）
├── app/tasks/         # Celery 异步任务
├── alembic/           # 数据库迁移
├── tests/             # pytest 测试
├── scripts/           # 工具脚本（如 seed.py）
└── requirements.txt
frontend/
├── src/api/           # Axios 客户端
├── src/layouts/       # 布局组件
├── src/router/        # 路由配置（含 beforeEach 守卫）
├── src/stores/        # Pinia 状态管理
├── src/views/         # 页面视图
└── src/components/    # Vue 组件
```

```

详细设计见 [docs/DESIGN.md](docs/DESIGN.md)。