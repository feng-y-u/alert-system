# 详细设计方案

**校园账号异常登录监测与告警平台** - 完整的设计文档

> 此文档包含项目的详细设计方案、数据模型、开发流程和代码模式。
> 核心框架信息请参考 [CLAUDE.md](../CLAUDE.md)

---

## 项目定位

这是一个**校园账号异常登录监测与告警平台**，属于**监控/运维类系统**，而非面向师生的业务系统。

### 核心架构

```
校园系统（被监控系统）
  │  学生/教师登录 → 产生登录日志
  │  POST /api/logs/login → 发送日志到监测平台
  ▼
校园账号异常登录监测平台（本项目）
  │  ● 接收并存储登录日志
  │  ● 检测异常登录行为（频率异常/设备异常/位置异常）
  │  ● 生成告警记录
  │  ● 管理员登录查看 Dashboard、日志、告警
  │  ● 处理告警（确认/解决）
  ▲
  │  管理员登录访问
  │  http://localhost:5173 → 登录 → Dashboard
```

### 关键角色

| 角色 | 说明 |
|------|------|
| **管理员** | 使用本监测平台的人，登录后可查看 Dashboard、登录日志、告警，并进行告警处理 |
| **校园系统用户** | 被监控系统的使用者（学生/教师），**不是本项目的用户**，他们的登录行为是本项目的监控数据来源 |

### 一句话概括

> 搭建一个监测平台，接入一个测试系统后，当测试系统出现异常登录问题时，管理员可以通过本平台收到警告并进行处理。

---

## 技术栈详情

### 后端（backend/）
- **FastAPI** — 现代、快速的Web框架，自动生成API文档
- **SQLAlchemy** — ORM框架，用于数据库操作
- **Alembic** — 数据库迁移工具
- **Celery** — 异步任务队列（发送邮件、定时检测）
- **Redis** — 缓存、会话管理、Celery消息代理
- **MySQL** — 主数据库，存储用户、登录日志、告警记录
- **Pandas** — 数据分析和处理
- **NumPy** — 数值计算
- **Scikit-learn** — 机器学习库（可选，用于复杂异常检测）

### 前端（frontend/）
- **Vue 3** — 渐进式JavaScript框架
- **Element Plus** — Vue 3企业级UI组件库
- **ECharts** — 专业数据可视化图表库
- **Axios** — HTTP客户端
- **Vue Router** — 路由管理
- **Pinia** — 状态管理

### 开发工具
- **Docker** — 容器化部署
- **Pytest** — Python测试框架
- **Black + Flake8** — 代码格式化
- **ESLint + Prettier** — JavaScript代码规范

## 项目结构

```
campus-login-monitor/
├── backend/                    # FastAPI后端
│   ├── app/
│   │   ├── api/               # API路由
│   │   │   └── v1/           # API版本1
│   │   ├── core/             # 核心配置
│   │   ├── models/           # SQLAlchemy数据模型
│   │   ├── schemas/          # Pydantic数据模式
│   │   ├── services/         # 业务逻辑层
│   │   ├── tasks/            # Celery异步任务
│   │   └── utils/            # 工具函数
│   ├── alembic/              # 数据库迁移
│   ├── tests/                # 测试
│   ├── requirements.txt      # Python依赖
│   └── alembic.ini          # Alembic配置
├── frontend/                   # Vue 3前端
│   ├── src/
│   │   ├── api/              # API客户端
│   │   ├── assets/           # 静态资源
│   │   ├── components/       # Vue组件
│   │   ├── layouts/          # 布局组件
│   │   ├── router/           # 路由配置
│   │   ├── stores/           # Pinia状态管理
│   │   ├── views/            # 页面视图
│   │   └── utils/            # 工具函数
│   ├── public/               # 公共静态文件
│   ├── package.json          # Node.js依赖
│   └── vite.config.js        # Vite配置
├── docker-compose.yml          # Docker编排
├── .env.example               # 环境变量示例
└── README.md                  # 项目说明
```

## 添加新功能的方法

**核心原则：一切功能模块化** — 每个功能独立为单独的模块/文件，单一职责，便于复用和测试。

### 后端添加新模块

```
步骤：
1. 创建 app/api/xxx.py → 定义 router
2. main.py 中 import 并 include_router
3. 完成
```

**示例：添加用户模块**

```python
# 1. 创建 app/api/users.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/users/")
def list_users():
    return {"users": []}

@router.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id}
```

```python
# 2. 在 app/main.py 中注册
from app.api.users import router as users_router

app.include_router(users_router, prefix="/api", tags=["用户管理"])
```

### 目录结构约定

| 目录 | 用途 | 示例 |
|------|------|------|
| `app/api/` | API路由，每个功能一个文件 | health.py, auth.py, logs.py |
| `app/core/` | 核心配置，数据库连接 | config.py, database.py, security.py |
| `app/models/` | SQLAlchemy数据模型，每个表一个文件 | user.py, login_log.py |
| `app/schemas/` | Pydantic数据模式，每个功能一个文件 | user.py, login_log.py |
| `app/services/` | 业务逻辑，每个功能一个文件 | auth.py, anomaly.py |
| `app/tasks/` | Celery异步任务，每个功能一个文件 | email.py, detection.py |

### 规范

- 每个文件只负责一个功能
- main.py 只做组装，不写业务逻辑
- 新功能先创建文件，再注册路由
- 复用已有模块，避免重复造轮子

## 核心功能实现

### 1. 管理员认证（第2周）
- **端点**：`POST /api/auth/login` — 管理员登录，返回 JWT token
- **端点**：`POST /api/auth/register` — 管理员创建新管理员（仅已登录管理员可调用）
- **认证方式**：JWT token，Bearer 头传递
- **密码存储**：passlib + bcrypt 哈希
- **角色**：仅 admin 角色，所有功能对登录用户开放
- **管理员初始化**：通过 seed 脚本创建默认管理员

### 2. 登录日志接收（第3周）
- **端点**：`POST /api/logs/login`
- **功能**：接收校园系统发送的登录日志数据（用户名、时间戳、IP地址、设备信息、登录状态）
- **存储**：写入MySQL的`login_logs`表
- **模拟数据**：开发阶段使用脚本生成模拟数据，模拟真实校园系统的登录行为

### 3. 异常检测（第4周）
- **频率异常**：检测短时间（如5分钟）内多次失败登录（阈值：>3次）
- **设备异常**：检测新设备/浏览器登录（与历史记录对比）
- **位置异常**：检测非校园IP登录（基础版可选）
- **工具**：使用Pandas进行数据分析

### 4. 告警生成（第5周）
- **触发**：异常检测后自动生成告警记录
- **存储**：写入`alerts`表（用户ID、异常类型、时间戳、详情）
- **状态**：待处理、已确认、已解决

### 5. 前端仪表盘（第6周）
- **登录日志列表**：显示最近的登录记录，支持筛选和搜索
- **告警列表**：显示异常登录告警，按优先级排序
- **统计图表**：登录次数趋势、异常类型分布
- **使用Element Plus + ECharts实现**

## 数据模型

### login_logs（登录日志表）
```sql
- id: 主键
- username: 用户名（被监控系统的用户）
- login_time: 登录时间戳
- ip_address: IP地址
- user_agent: 浏览器/设备信息
- login_status: 成功/失败
- location: 登录位置（可选）
- created_at: 记录创建时间
```

### alerts（告警表）
```sql
- id: 主键
- user_id: 关联用户ID
- alert_type: 异常类型（frequency/device/location）
- alert_message: 告警详情
- severity: 优先级（low/medium/high）
- status: 状态（pending/acknowledged/resolved）
- created_at: 告警时间
- resolved_at: 解决时间（可选）
```

### users（管理员表）
```sql
- id: 主键
- username: 管理员用户名
- email: 邮箱地址
- hashed_password: 加密密码
- role: 角色（固定为 admin）
- is_active: 是否激活
- created_at: 创建时间
```

## 开发流程

### 实习版开发计划（8周）

**第1周：项目搭建与基础架构** ✅ 已完成
- 搭建后端FastAPI项目框架
- 配置MySQL和Redis
- 创建基础数据库模型
- 搭建Vue 3项目框架
- 配置开发环境（Docker Compose）

**第2周：管理员认证** 👈 当前
- 实现管理员登录API（JWT token）
- 实现管理员创建API（仅管理员可调用）
- 编写 seed 脚本初始化默认管理员
- 开发前端登录页面对接真实API
- 添加路由守卫（未登录跳转登录页）

**第3周：登录日志管理**
- 实现登录日志接收API（POST /api/logs/login）
- 创建模拟数据生成脚本
- 实现登录日志查询API（GET /api/logs/login）
- 开发前端登录日志列表页面

**第4周：异常检测基础**
- 实现频率异常检测逻辑
- 实现设备异常检测逻辑
- 集成Pandas进行数据分析
- 编写异常检测单元测试

**第5周：告警系统**
- 实现告警生成和存储
- 实现告警查询API
- 集成邮件告警功能
- 开发前端告警列表页面

**第6周：前端仪表盘**
- 开发统计图表（ECharts）
- 实现登录次数趋势图
- 实现异常类型分布图
- 完善筛选和搜索功能

**第7周：功能完善**
- 添加实时告警通知
- 优化异常检测算法
- 完善错误处理
- 性能优化

**第8周：测试与部署**
- 编写集成测试
- Docker容器化部署
- 编写项目文档
- 代码审查与优化

### 毕设版扩展计划（后续）
- 地理位置异常检测（集成IP地址库）
- 实时监控（WebSocket推送）
- 高级统计与报告生成
- 用户行为分析
- 告警规则配置界面
- 移动端适配

## 关键代码模式

### 后端API路由模式
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.login_log import LoginLogCreate, LoginLogResponse

router = APIRouter()

@router.post("/login-logs/", response_model=LoginLogResponse)
def create_login_log(log: LoginLogCreate, db: Session = Depends(get_db)):
    # 实现逻辑
    pass
```

### 异常检测模式
```python
import pandas as pd
from datetime import datetime, timedelta

def detect_frequency_anomaly(user_logs: pd.DataFrame, threshold: int = 3, window_minutes: int = 5) -> bool:
    """检测频率异常：短时间内多次失败登录"""
    now = datetime.now()
    window_start = now - timedelta(minutes=window_minutes)

    recent_failures = user_logs[
        (user_logs['login_time'] >= window_start) &
        (user_logs['login_status'] == 'failure')
    ]

    return len(recent_failures) > threshold
```

### 前端API调用模式
```javascript
// api/login.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 10000,
})

export function getLoginLogs(params) {
  return api.get('/api/login-logs/', { params })
}

export function getAlerts(params) {
  return api.get('/api/alerts/', { params })
}
```

## 环境变量配置

创建`.env`文件（参考`.env.example`）：

```bash
# 后端
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/campus_monitor
REDIS_URL=redis://localhost:6479/0
SECRET_KEY=your-secret-key-here
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USER=your-email@example.com
EMAIL_PASSWORD=your-email-password

# 前端
VITE_API_BASE_URL=http://localhost:8000
```

## 注意事项

1. **数据隐私** — 登录日志包含敏感信息，确保数据加密存储和传输
2. **性能考虑** — Pandas分析大量日志时考虑使用数据库查询优化
3. **异步任务** — 邮件发送、定时检测等耗时操作使用Celery异步处理
4. **错误处理** — API返回标准错误响应，前端显示友好错误提示
5. **代码规范** — 后端使用Black格式化，前端使用Prettier格式化
6. **本项目是监控平台** — 不要混淆"被监控系统的用户"和"本平台的管理员"两个角色

## 扩展资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Vue 3官方文档](https://vuejs.org/)
- [Element Plus文档](https://element-plus.org/)
- [ECharts文档](https://echarts.apache.org/)
- [Celery文档](https://docs.celeryq.dev/)