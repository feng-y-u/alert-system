# 校园账号异常登录监测与告警平台

安全审计与日志分析系统，用于监测校园系统的登录行为，检测异常登录并发送告警。

> 定位：监控/运维类平台。管理员登录后监控校园系统的登录日志，发现异常时处理告警。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI + SQLAlchemy + Alembic + Celery + Redis |
| 数据库 | MySQL 8.0 |
| 前端 | Vue 3 + Element Plus + ECharts + Pinia + Vue Router |
| 分析 | Pandas + NumPy |

## 快速开始

### Docker 一键部署（推荐）

```bash
docker-compose up -d
```

自动启动 MySQL、Redis、后端、前端、Celery Worker、Celery Beat 六个服务。

| 服务 | 端口 | 说明 |
|---|---|---|
| 前端 | `80` | Nginx 托管静态文件 + 反向代理 |
| 后端 | `8000` | FastAPI API 服务 |
| MySQL | `8881` | 数据库 |
| Redis | `8880` | 缓存 + Celery Broker |

首次启动后自动创建管理员账号：`admin` / `admin123`

### 本地开发

#### 1. 启动基础服务

```bash
docker-compose up -d    # 启动 MySQL 8.0 + Redis 7
```

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

#### 4. Celery 异步任务（可选）

```bash
cd backend
celery -A app.tasks worker --loglevel=info     # Worker
celery -A app.tasks beat --loglevel=info       # 定时调度
```

## 环境变量

复制模板文件并修改：

```bash
cp backend/.env.example backend/.env
```

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DATABASE_URL` | MySQL 连接地址 | `localhost:8881` |
| `REDIS_URL` | Redis 连接地址 | `localhost:8880` |
| `SECRET_KEY` | JWT 签名密钥 | `change-me` |
| `API_KEY` | 日志写入 API Key | `dev-api-key-change-in-production` |
| `EMAIL_*` | 邮件告警 SMTP 配置 | 未启用 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | `1440` |

## 测试

```bash
cd backend
python -m pytest tests/ -v
```

测试覆盖：
- 健康检查
- 密码哈希 / JWT 认证
- 频率异常检测 / 设备异常检测 / 告警去重
- 认证 → 日志写入 → 检测 → 告警 API → 统计 全流程集成测试
- SSE 推送事件发布

## 项目结构

```
backend/
├── app/
│   ├── api/             API 路由
│   ├── core/            配置 + 数据库 + 安全 + 依赖注入 + Redis
│   ├── models/          SQLAlchemy ORM 模型
│   ├── schemas/         Pydantic 模式
│   ├── services/        业务逻辑
│   └── tasks/           Celery 异步任务（检测、邮件）
├── alembic/             数据库迁移
├── tests/               pytest 测试
├── scripts/             seed.py 工具脚本
├── docker-entrypoint.sh 容器启动入口
├── Dockerfile
└── requirements.txt
frontend/
├── src/
│   ├── api/             Axios 客户端 + 拦截器
│   ├── composables/     可复用逻辑（在线检测、重试）
│   ├── components/      Vue 组件（图表、通用、告警、日志）
│   ├── layouts/         布局组件
│   ├── router/          路由配置
│   ├── stores/          Pinia 状态管理（认证、通知/SSE）
│   └── views/           页面视图
├── nginx.conf           生产环境 Nginx 配置
├── Dockerfile           多阶段构建（Node + Nginx）
└── package.json
docker-compose.yml       全栈编排
```

详细设计见 [docs/DESIGN.md](docs/DESIGN.md)，UI 规范见 [docs/UI.md](docs/UI.md)。
