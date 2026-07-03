# 校园账号异常登录监测与告警平台

安全审计与日志分析系统，用于检测校园账号的异常登录行为并发送告警。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | MySQL 8.0 |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia |
| 分析 | Pandas + NumPy |

## 快速开始

### 1. 启动基础服务

```bash
docker-compose up -d    # 启动 MySQL + Redis
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head    # 应用数据库迁移
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

## 开发计划（8 周）

| 周次 | 内容 |
|------|------|
| 第 1 周 | 项目搭建与基础架构 |
| 第 2 周 | 用户认证与权限 |
| 第 3 周 | 登录日志管理 |
| 第 4 周 | 异常检测基础 |
| 第 5 周 | 告警系统 |
| 第 6 周 | 前端仪表盘 |
| 第 7 周 | 功能完善 |
| 第 8 周 | 测试与部署 |

详细设计见 [docs/DESIGN.md](docs/DESIGN.md)。