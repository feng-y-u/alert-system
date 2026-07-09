# 第3周：登录日志管理设计文档

> 日期: 2026-07-09  
> 状态: 待实现  
> 依赖: 第2周（管理员认证）已完成

---

## 1. 目标

实现登录日志的接收、存储和查询功能。

- **后端**: 提供日志接收 API（API Key 认证）和查询 API（JWT 认证）
- **前端**: 实现日志列表页面，支持筛选和分页

---

## 2. 后端设计

### 2.1 模块结构

```
backend/app/
├── api/
│   └── logs.py              # 新增：日志路由
├── services/
│   └── logs.py              # 新增：日志业务逻辑
├── schemas/
│   └── logs_query.py        # 新增：查询参数 Schema
├── core/
│   └── deps.py              # 修改：添加 API Key 依赖
└── models/
    └── login_log.py         # 已有
```

### 2.2 数据库索引

为支持筛选和排序性能，需确保以下索引已建立（在 Alembic 迁移中）：

```python
# login_logs 表索引
- username: 普通索引（支持模糊查询）
- ip_address: 普通索引（精确匹配）
- login_time: 普通索引（时间范围查询 + 排序）
- login_status: 普通索引（状态筛选）
```

### 2.2 API 端点

#### POST /api/logs — 接收日志

**认证方式**: API Key（Header: `X-API-Key`）

**请求体**:
```json
{
  "username": "zhangsan",
  "login_time": "2026-07-09T14:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "login_status": "success",
  "location": "教学楼A"
}
```

**成功响应** (201):
```json
{
  "id": 1,
  "username": "zhangsan",
  "login_time": "2026-07-09T14:30:00Z",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "login_status": "success",
  "location": "教学楼A",
  "created_at": "2026-07-09T14:30:01Z",
  "updated_at": "2026-07-09T14:30:01Z"
}
```

**错误响应**:
- 401: API Key 无效
- 422: 请求参数校验失败

---

#### GET /api/logs — 查询日志

**认证方式**: JWT（Bearer Token）

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 模糊匹配用户名（支持 LIKE %keyword%） |
| ip_address | string | 否 | 精确匹配 IP |
| login_status | string | 否 | success 或 failure |
| start_time | datetime | 否 | ISO 8601 格式，开始时间 |
| end_time | datetime | 否 | ISO 8601 格式，结束时间 |
| skip | int | 否 | 偏移量，默认 0 |
| limit | int | 否 | 每页数量，默认 50，最大 100 |

**成功响应** (200):
```json
{
  "items": [
    {
      "id": 1,
      "username": "zhangsan",
      "login_time": "2026-07-09T14:30:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "login_status": "success",
      "location": "教学楼A",
      "created_at": "2026-07-09T14:30:01Z",
      "updated_at": "2026-07-09T14:30:01Z"
    }
  ],
  "total": 100,
  "skip": 0,
  "limit": 50
}
```

---

### 2.3 Schema 定义

**`schemas/logs_query.py`**:
```python
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class LogQueryParams(BaseModel):
    """日志查询参数"""
    username: Optional[str] = Field(None, description="模糊匹配用户名")
    ip_address: Optional[str] = None
    login_status: Optional[str] = Field(None, pattern="^(success|failure)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)

    @model_validator(mode='after')
    def check_time_range(self):
        """校验时间范围"""
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise ValueError("start_time 不能晚于 end_time")
        return self


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: list[LoginLogResponse]
    total: int
    skip: int
    limit: int
```

---

### 2.4 依赖注入

**`core/deps.py` 新增**:
```python
from fastapi import Header, HTTPException, status

from app.core.config import settings


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> str:
    """验证 API Key"""
    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return x_api_key
```

**`core/config.py` 新增**:
```python
API_KEY: str = "dev-api-key-change-in-production"
```

> ⚠️ **安全提示**: 生产环境务必通过环境变量注入强随机 API Key，并考虑定期轮换。

---

### 2.5 Service 层

**`services/logs.py`**:
```python
from datetime import datetime
from typing import Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate


def build_log_query(
    db: Session,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    login_status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """构建日志查询"""
    query = db.query(LoginLog)
    
    if username:
        query = query.filter(LoginLog.username.contains(username))
    if ip_address:
        query = query.filter(LoginLog.ip_address == ip_address)
    if login_status:
        query = query.filter(LoginLog.login_status == login_status)
    if start_time:
        query = query.filter(LoginLog.login_time >= start_time)
    if end_time:
        query = query.filter(LoginLog.login_time <= end_time)
    
    return query.order_by(desc(LoginLog.login_time))


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    **filters
) -> tuple[list[LoginLog], int]:
    """获取日志列表和总数"""
    query = build_log_query(db, **filters)
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    return logs, total


def create_log(db: Session, log_data: LoginLogCreate) -> LoginLog:
    """创建日志记录"""
    log = LoginLog(**log_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
```

---

### 2.6 API 路由层

**`api/logs.py`**:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_api_key
from app.models.user import User
from app.schemas.login_log import LoginLogCreate, LoginLogResponse
from app.schemas.logs_query import LogQueryParams, LogListResponse
from app.services.logs import create_log, get_logs

router = APIRouter()


@router.post("/logs", response_model=LoginLogResponse, status_code=201)
def receive_log(
    data: LoginLogCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """接收登录日志（校园系统调用）"""
    return create_log(db, data)


@router.get("/logs", response_model=LogListResponse)
def list_logs(
    params: LogQueryParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询日志列表（管理员调用）"""
    logs, total = get_logs(
        db,
        skip=params.skip,
        limit=params.limit,
        username=params.username,
        ip_address=params.ip_address,
        login_status=params.login_status,
        start_time=params.start_time,
        end_time=params.end_time,
    )
    return {
        "items": logs,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
    }
```

---

## 3. 前端设计

### 3.1 模块结构

```
frontend/src/
├── views/
│   └── LoginLogs.vue           # 日志列表页面
├── components/
│   ├── logs/
│   │   ├── LogFilter.vue         # 筛选组件
│   │   ├── LogTable.vue          # 表格组件
│   │   └── LogPagination.vue     # 分页组件
│   └── common/
│       └── StatusTag.vue         # 状态标签组件
└── api/
    └── logs.js                   # 日志 API 封装
```

### 3.2 页面布局

遵循 UI.md 规范：
- 页面边距: 32px
- 卡片圆角: 12px
- 表格行高: 64px

**布局结构**:
```
┌─────────────────────────────────────────┐
│  标题: 登录日志                           │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐ │
│  │ 筛选区                               │ │
│  │ 用户名 [输入框] IP [输入框] 状态 [下拉] │ │
│  │ 时间 [日期选择] [查询按钮]            │ │
│  └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────────┐ │
│  │ 表格区                               │ │
│  │ 用户名 │ 登录时间 │ IP │ 状态 │ 位置   │ │
│  │ ...                                │ │
│  └─────────────────────────────────────┘ │
├─────────────────────────────────────────┤
│  分页: < 1 2 3 ... 10 >                  │
└─────────────────────────────────────────┘
```

### 3.3 组件设计

**`LogFilter.vue`**:
- Props: `filters` (当前筛选值)
- Emits: `search` (点击查询时触发)
- 包含字段：用户名、IP地址、登录状态、时间范围

**`LogTable.vue`**:
- Props: `logs` (日志数组)
- 列定义：
  - 用户名: 左对齐
  - 登录时间: 格式化为 "2026-07-09 14:30"
  - IP地址: 等宽字体
  - 状态: 使用 `StatusTag` 组件（success=绿色, failure=红色）
  - 位置: 左对齐

**`LogPagination.vue`**:
- Props: `total`, `currentPage`, `pageSize`
- Emits: `change(page, pageSize)` (页码或每页数量变化时触发)
- 内部计算 `skip = (page - 1) * pageSize`

### 3.4 API 封装

**`api/logs.js`**:
```javascript
import api from './index'

export function getLogs(params) {
  return api.get('/api/logs', { params })
}

// 注: receiveLog 仅供校园系统后端调用，前端无需使用
// export function receiveLog(data, apiKey) {
//   return api.post('/api/logs', data, {
//     headers: { 'X-API-Key': apiKey }
//   })
// }
```

---

## 4. 路由配置

**`router/index.js` 修改**:
```javascript
{
  path: '/login-logs',
  name: 'LoginLogs',
  component: () => import('../views/LoginLogs.vue'),
  meta: { requiresAuth: true }
}
```

同时更新 `MainLayout.vue` 中的菜单项，移除 `disabled`。

---

## 5. 测试要点

### 后端测试
- `POST /api/logs` 正确创建日志
- `POST /api/logs` API Key 无效时返回 401
- `GET /api/logs` 各筛选条件组合正确
- `GET /api/logs` 分页逻辑正确

### 前端测试
- 筛选条件正确传递给 API
- 表格正确渲染数据
- 分页切换正确更新数据
- 状态标签颜色正确

---

## 6. 验收标准

- [ ] `POST /api/logs` 可接收日志并返回 201
- [ ] `GET /api/logs` 支持所有筛选条件和分页
- [ ] 前端页面可查看日志列表
- [ ] 前端筛选功能正常工作
- [ ] 前端分页功能正常工作
- [ ] 侧边栏菜单项可正常点击跳转

---

## 7. 文件清单

### 新增文件
- `backend/app/api/logs.py`
- `backend/app/services/logs.py`
- `backend/app/schemas/logs_query.py`
- `frontend/src/views/LoginLogs.vue`
- `frontend/src/components/logs/LogFilter.vue`
- `frontend/src/components/logs/LogTable.vue`
- `frontend/src/components/logs/LogPagination.vue`
- `frontend/src/components/common/StatusTag.vue`
- `frontend/src/api/logs.js`

### 修改文件
- `backend/app/core/deps.py` — 添加 `verify_api_key`
- `backend/app/core/config.py` — 添加 `API_KEY`
- `backend/app/main.py` — 注册 logs 路由
- `frontend/src/router/index.js` — 添加路由
- `frontend/src/layouts/MainLayout.vue` — 移除菜单 disabled

---

设计确认后，将调用 `writing-plans` 生成详细实施计划。