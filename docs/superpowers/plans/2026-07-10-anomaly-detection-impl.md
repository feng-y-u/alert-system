# 第四周：异常检测模块 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现异常检测系统，包括频率异常检测、设备异常检测、实时异步检测、定时增量检测、告警去重

**Architecture:** 检测逻辑封装在 services/detection.py，实时检测通过 Celery 异步任务触发，定时检测通过 Celery Beat 每小时运行，告警生成前进行去重检查

**Tech Stack:** FastAPI + SQLAlchemy + Celery + Pandas

## Global Constraints

- 使用 `app.core.database.SessionLocal` 获取数据库会话
- 所有数据库操作后必须 `db.commit()` 和 `db.refresh()`
- Celery 任务使用 `app.tasks.celery_app` 装饰器
- 时间使用 `datetime.utcnow()` 获取 UTC 时间
- 索引命名使用 `idx_表名_字段1_字段2` 格式
- 告警去重时间窗口：24 小时
- 滑动窗口计算使用 `login_time >= now - timedelta(minutes=5)`

---

### Task 1: 数据库迁移 — 添加 log_id 字段和索引

**Files:**
- Create: `backend/alembic/versions/2026_07_10_add_log_id_to_alerts.py`
- Modify: `backend/app/models/alert.py`
- Modify: `backend/app/models/login_log.py`

**Interfaces:**
- Consumes: SQLAlchemy Column, ForeignKey, Index
- Produces: Alert.log_id 字段, login_logs 复合索引

- [ ] **Step 1: 创建 Alembic 迁移文件**

```python
# backend/alembic/versions/2026_07_10_add_log_id_to_alerts.py
"""add log_id to alerts and add indexes

Revision ID: 2026_07_10_add_log_id_to_alerts
Revises: 2e7a3f8b1c4d
Create Date: 2026-07-10 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2026_07_10_add_log_id_to_alerts'
down_revision: Union[str, None] = '2e7a3f8b1c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 log_id 字段到 alerts 表
    op.add_column('alerts', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_alerts_log_id_login_logs',
        'alerts', 'login_logs',
        ['log_id'], ['id']
    )
    
    # 创建 alerts 表索引
    op.create_index(
        'idx_alerts_username_alert_type_status',
        'alerts',
        ['username', 'alert_type', 'status']
    )
    
    # 创建 login_logs 表复合索引
    op.create_index(
        'idx_login_logs_username_login_time',
        'login_logs',
        ['username', 'login_time']
    )


def downgrade() -> None:
    op.drop_index('idx_login_logs_username_login_time', table_name='login_logs')
    op.drop_index('idx_alerts_username_alert_type_status', table_name='alerts')
    op.drop_constraint('fk_alerts_log_id_login_logs', 'alerts', type_='foreignkey')
    op.drop_column('alerts', 'log_id')
```

- [ ] **Step 2: 修改 Alert 模型**

```python
# backend/app/models/alert.py
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    __table_args__ = (
        Index("idx_alerts_username_alert_type_status", "username", "alert_type", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    log_id = Column(Integer, ForeignKey("login_logs.id"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)
    alert_message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # 关联关系
    log = relationship("LoginLog", backref="alerts")
```

- [ ] **Step 3: 修改 LoginLog 模型添加索引**

```python
# backend/app/models/login_log.py
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Index

from app.core.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"
    
    __table_args__ = (
        Index("idx_login_logs_username_login_time", "username", "login_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    login_time = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500))
    login_status = Column(String(20), nullable=False)
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 4: 运行迁移**

```bash
cd e:/实习/backend
$env:PYTHONPATH = "E:\实习\backend"
alembic upgrade head
```

Expected: 迁移成功，log_id 字段和索引已创建

- [ ] **Step 5: 提交**

```bash
cd e:/实习
git add backend/alembic/versions/2026_07_10_add_log_id_to_alerts.py backend/app/models/alert.py backend/app/models/login_log.py
git commit -m "feat: add log_id to alerts and create indexes for anomaly detection"
```

---

### Task 2: 更新 Alert Schema

**Files:**
- Modify: `backend/app/schemas/alert.py`

**Interfaces:**
- Consumes: Pydantic BaseModel
- Produces: AlertCreate, AlertResponse with log_id

- [ ] **Step 1: 更新 AlertCreate**

```python
# backend/app/schemas/alert.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    username: str
    log_id: int | None = None
    alert_type: str
    alert_message: str
    severity: str
```

- [ ] **Step 2: 更新 AlertResponse**

```python
class AlertResponse(BaseModel):
    id: int
    username: str
    log_id: int | None = None
    alert_type: str
    alert_message: str
    severity: str
    status: str
    created_at: datetime
    updated_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 3: 添加 AlertListResponse**

```python
class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    skip: int
    limit: int
```

- [ ] **Step 4: 提交**

```bash
cd e:/实习
git add backend/app/schemas/alert.py
git commit -m "feat: update Alert schemas with log_id and AlertListResponse"
```

---

### Task 3: 实现检测服务 detection.py

**Files:**
- Create: `backend/app/services/detection.py`

**Interfaces:**
- Consumes: SQLAlchemy Session, LoginLog, Alert models
- Produces: detect_frequency_anomaly, detect_device_anomaly, should_create_alert functions

- [ ] **Step 1: 创建检测服务文件**

```python
# backend/app/services/detection.py
"""异常检测服务"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.schemas.alert import AlertCreate


def detect_frequency_anomaly(
    db: Session,
    username: str,
    log_id: Optional[int] = None,
    since: Optional[datetime] = None
) -> Optional[Alert]:
    """
    检测频率异常：同一用户5分钟内登录超过10次
    
    Args:
        db: 数据库会话
        username: 用户名
        log_id: 实时检测时传入，用于定位当前日志
        since: 定时检测时传入，用于增量检测
    
    Returns:
        如果检测到异常返回 Alert，否则返回 None
    """
    # 确定时间窗口
    if log_id:
        # 实时检测：获取当前日志时间
        current_log = db.query(LoginLog).filter(LoginLog.id == log_id).first()
        if not current_log:
            return None
        end_time = current_log.login_time
    else:
        # 定时检测：使用当前时间
        end_time = datetime.utcnow()
    
    start_time = end_time - timedelta(minutes=5)
    
    # 查询时间窗口内的登录次数
    count = db.query(func.count(LoginLog.id)).filter(
        LoginLog.username == username,
        LoginLog.login_time >= start_time,
        LoginLog.login_time <= end_time
    ).scalar()
    
    # 判断是否异常
    if count < 10:
        return None
    
    # 确定严重级别
    if count <= 30:
        severity = "medium"
        message = f"用户 {username} 在5分钟内登录 {count} 次，可能存在异常"
    else:
        severity = "high"
        message = f"用户 {username} 在5分钟内登录 {count} 次，疑似暴力破解攻击"
    
    # 检查是否应该创建告警（去重）
    if not should_create_alert(db, username, "frequency"):
        return None
    
    # 创建告警
    alert_data = AlertCreate(
        username=username,
        log_id=log_id,
        alert_type="frequency",
        alert_message=message,
        severity=severity
    )
    
    alert = Alert(**alert_data.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert


def detect_device_anomaly(
    db: Session,
    username: str,
    log_id: Optional[int] = None,
    since: Optional[datetime] = None
) -> Optional[Alert]:
    """
    检测设备异常：同一用户1小时内User-Agent或IP发生变化
    
    Args:
        db: 数据库会话
        username: 用户名
        log_id: 实时检测时传入
        since: 定时检测时传入
    
    Returns:
        如果检测到异常返回 Alert，否则返回 None
    """
    # 确定时间窗口
    if log_id:
        current_log = db.query(LoginLog).filter(LoginLog.id == log_id).first()
        if not current_log:
            return None
        end_time = current_log.login_time
    else:
        end_time = datetime.utcnow()
    
    start_time = end_time - timedelta(hours=1)
    
    # 查询时间窗口内的不同设备（按user_agent + ip_address组合）
    logs = db.query(LoginLog).filter(
        LoginLog.username == username,
        LoginLog.login_time >= start_time,
        LoginLog.login_time <= end_time
    ).all()
    
    # 统计不同设备数
    devices = set()
    for log in logs:
        device_key = f"{log.user_agent}|{log.ip_address}"
        devices.add(device_key)
    
    device_count = len(devices)
    
    # 判断是否异常（2个及以上设备）
    if device_count < 2:
        return None
    
    # 确定严重级别
    if device_count == 2:
        severity = "medium"
        message = f"用户 {username} 在1小时内使用2个不同设备登录"
    else:
        severity = "high"
        message = f"用户 {username} 在1小时内使用 {device_count} 个不同设备登录，疑似账号共享或被盗"
    
    # 检查是否应该创建告警（去重）
    if not should_create_alert(db, username, "device"):
        return None
    
    # 创建告警
    alert_data = AlertCreate(
        username=username,
        log_id=log_id,
        alert_type="device",
        alert_message=message,
        severity=severity
    )
    
    alert = Alert(**alert_data.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    
    return alert


def should_create_alert(
    db: Session,
    username: str,
    alert_type: str
) -> bool:
    """
    检查是否应该创建新告警（去重逻辑）
    
    24小时内是否存在 pending 的同类告警
    
    Args:
        db: 数据库会话
        username: 用户名
        alert_type: 告警类型
    
    Returns:
        True 表示应该创建新告警，False 表示已存在未处理的同类告警
    """
    since = datetime.utcnow() - timedelta(hours=24)
    
    existing = db.query(Alert).filter(
        Alert.username == username,
        Alert.alert_type == alert_type,
        Alert.status == "pending",
        Alert.created_at >= since
    ).first()
    
    return existing is None
```

- [ ] **Step 2: 提交**

```bash
cd e:/实习
git add backend/app/services/detection.py
git commit -m "feat: implement anomaly detection service with frequency and device detection"
```

---

### Task 4: 实现 Celery 检测任务

**Files:**
- Modify: `backend/app/tasks/detection.py`

**Interfaces:**
- Consumes: celery_app, detection service functions
- Produces: detect_anomaly_for_log, run_anomaly_detection tasks

- [ ] **Step 1: 实现实时检测任务**

```python
# backend/app/tasks/detection.py
"""Celery 异步任务：异常检测"""

from datetime import datetime

from app.core.database import SessionLocal
from app.models.login_log import LoginLog
from app.services.detection import detect_frequency_anomaly, detect_device_anomaly
from app.tasks import celery_app


@celery_app.task
def detect_anomaly_for_log(log_id: int) -> str:
    """
    实时检测单条日志的异常
    
    Args:
        log_id: 登录日志ID
    
    Returns:
        检测结果的描述字符串
    """
    db = SessionLocal()
    try:
        log = db.query(LoginLog).filter(LoginLog.id == log_id).first()
        if not log:
            return f"Log {log_id} not found"
        
        results = []
        
        # 频率检测
        freq_alert = detect_frequency_anomaly(db, log.username, log_id)
        if freq_alert:
            results.append(f"Frequency alert created: {freq_alert.id}")
        
        # 设备检测
        device_alert = detect_device_anomaly(db, log.username, log_id)
        if device_alert:
            results.append(f"Device alert created: {device_alert.id}")
        
        if results:
            return "; ".join(results)
        return "No anomaly detected"
    
    except Exception as e:
        return f"Error during detection: {str(e)}"
    
    finally:
        db.close()
```

- [ ] **Step 2: 实现定时检测任务**

```python
import redis
from app.core.config import settings

# Redis 客户端用于存储上次检测时间
redis_client = redis.from_url(settings.REDIS_URL)

LAST_CHECK_KEY = "anomaly_detection:last_check_time"


def get_last_check_time() -> datetime:
    """获取上次检测时间"""
    last_check = redis_client.get(LAST_CHECK_KEY)
    if last_check:
        return datetime.fromisoformat(last_check.decode())
    # 默认返回1小时前
    return datetime.utcnow() - timedelta(hours=1)


def set_last_check_time(time: datetime):
    """设置上次检测时间"""
    redis_client.set(LAST_CHECK_KEY, time.isoformat())


@celery_app.task
def run_anomaly_detection() -> str:
    """
    每小时运行增量异常检测
    
    只检测上次检测后产生的新日志
    
    Returns:
        检测结果的描述字符串
    """
    db = SessionLocal()
    try:
        # 获取上次检测时间
        last_check_time = get_last_check_time()
        current_time = datetime.utcnow()
        
        # 获取上次检测后产生日志的所有用户
        users = db.query(LoginLog.username).filter(
            LoginLog.created_at >= last_check_time
        ).distinct().all()
        
        users = [u[0] for u in users]
        
        total_alerts = 0
        
        for username in users:
            # 频率检测
            freq_alert = detect_frequency_anomaly(
                db, username, log_id=None, since=last_check_time
            )
            if freq_alert:
                total_alerts += 1
            
            # 设备检测
            device_alert = detect_device_anomaly(
                db, username, log_id=None, since=last_check_time
            )
            if device_alert:
                total_alerts += 1
        
        # 更新上次检测时间
        set_last_check_time(current_time)
        
        return f"Anomaly detection completed. Checked {len(users)} users, created {total_alerts} alerts."
    
    except Exception as e:
        return f"Error during anomaly detection: {str(e)}"
    
    finally:
        db.close()
```

- [ ] **Step 3: 提交**

```bash
cd e:/实习
git add backend/app/tasks/detection.py
git commit -m "feat: implement Celery tasks for real-time and scheduled anomaly detection"
```

---

### Task 5: 修改日志服务添加实时检测钩子

**Files:**
- Modify: `backend/app/services/logs.py`

**Interfaces:**
- Consumes: detection task
- Produces: create_log triggers async detection

- [ ] **Step 1: 导入 Celery 任务**

```python
# backend/app/services/logs.py
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate
from app.tasks.detection import detect_anomaly_for_log


# ... 其他函数不变 ...


def create_log(db: Session, log_data: LoginLogCreate) -> LoginLog:
    """创建日志记录并触发异步异常检测"""
    log = LoginLog(**log_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # 触发异步异常检测
    detect_anomaly_for_log.delay(log.id)
    
    return log
```

- [ ] **Step 2: 提交**

```bash
cd e:/实习
git add backend/app/services/logs.py
git commit -m "feat: trigger async anomaly detection after creating log"
```

---

### Task 6: 实现告警 API

**Files:**
- Create: `backend/app/api/alerts.py`

**Interfaces:**
- Consumes: Alert service, schemas
- Produces: GET /api/alerts, PUT /api/alerts/{id}

- [ ] **Step 1: 创建告警 API**

```python
# backend/app/api/alerts.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertResponse, AlertUpdate

router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status: pending/acknowledged/resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: low/medium/high"),
    username: Optional[str] = Query(None, description="Filter by username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询告警列表"""
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if username:
        query = query.filter(Alert.username == username)
    
    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": alerts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个告警详情"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    update_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新告警状态"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # 更新状态
    if update_data.status:
        alert.status = update_data.status
        if update_data.status == "resolved":
            from datetime import datetime
            alert.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(alert)
    return alert
```

- [ ] **Step 2: 注册路由**

```python
# backend/app/main.py
# 在现有导入后添加
from app.api.alerts import router as alerts_router

# 在 include_router 部分添加
app.include_router(alerts_router, prefix=settings.API_V1_PREFIX, tags=["告警"])
```

- [ ] **Step 3: 提交**

```bash
cd e:/实习
git add backend/app/api/alerts.py backend/app/main.py
git commit -m "feat: implement alerts API with list, get, update endpoints"
```

---

### Task 7: 配置 Celery Beat 定时任务

**Files:**
- Modify: `backend/app/tasks/__init__.py`

**Interfaces:**
- Consumes: Celery app configuration
- Produces: Beat schedule for hourly detection

- [ ] **Step 1: 添加 Beat 配置**

```python
# backend/app/tasks/__init__.py
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "campus_monitor",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email", "app.tasks.detection"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    # Beat 定时任务配置
    beat_schedule={
        "anomaly-detection-every-hour": {
            "task": "app.tasks.detection.run_anomaly_detection",
            "schedule": 3600.0,  # 每小时运行一次（秒）
        },
    },
)
```

- [ ] **Step 2: 提交**

```bash
cd e:/实习
git add backend/app/tasks/__init__.py
git commit -m "feat: configure Celery Beat for hourly anomaly detection"
```

---

### Task 8: 编写测试

**Files:**
- Create: `backend/tests/test_detection.py`

**Interfaces:**
- Consumes: pytest, detection service functions
- Produces: Test cases for detection logic

- [ ] **Step 1: 创建测试文件**

```python
# backend/tests/test_detection.py
"""异常检测服务测试"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate
from app.services.detection import (
    detect_device_anomaly,
    detect_frequency_anomaly,
    should_create_alert,
)
from app.services.logs import create_log


def test_detect_frequency_anomaly_normal(db: Session):
    """测试正常登录频率（不触发告警）"""
    # 创建5条登录记录（间隔1分钟）
    for i in range(5):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=datetime.utcnow() - timedelta(minutes=i),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            login_status="success"
        )
        create_log(db, log_data)
    
    # 检测
    alert = detect_frequency_anomaly(db, "testuser")
    assert alert is None


def test_detect_frequency_anomaly_medium(db: Session):
    """测试中等级别频率异常（10-30次）"""
    # 创建15条登录记录（5分钟内）
    base_time = datetime.utcnow()
    for i in range(15):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(seconds=i*20),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            login_status="success"
        )
        create_log(db, log_data)
    
    # 检测
    alert = detect_frequency_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "medium"
    assert alert.alert_type == "frequency"


def test_detect_frequency_anomaly_high(db: Session):
    """测试高级别频率异常（>30次）"""
    # 创建35条登录记录（5分钟内）
    base_time = datetime.utcnow()
    for i in range(35):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(seconds=i*8),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            login_status="success"
        )
        create_log(db, log_data)
    
    # 检测
    alert = detect_frequency_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "high"


def test_detect_device_anomaly_single_device(db: Session):
    """测试单设备登录（不触发告警）"""
    base_time = datetime.utcnow()
    for i in range(3):
        log_data = LoginLogCreate(
            username="testuser",
            login_time=base_time - timedelta(minutes=i*10),
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0)",
            login_status="success"
        )
        create_log(db, log_data)
    
    alert = detect_device_anomaly(db, "testuser")
    assert alert is None


def test_detect_device_anomaly_multiple_devices(db: Session):
    """测试多设备登录（触发告警）"""
    base_time = datetime.utcnow()
    
    # 设备1
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=30),
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0)",
        login_status="success"
    )
    create_log(db, log_data)
    
    # 设备2
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=20),
        ip_address="192.168.1.2",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS)",
        login_status="success"
    )
    create_log(db, log_data)
    
    # 设备3
    log_data = LoginLogCreate(
        username="testuser",
        login_time=base_time - timedelta(minutes=10),
        ip_address="192.168.1.3",
        user_agent="Mozilla/5.0 (Linux; Android)",
        login_status="success"
    )
    create_log(db, log_data)
    
    alert = detect_device_anomaly(db, "testuser")
    assert alert is not None
    assert alert.severity == "high"
    assert "3 个不同设备" in alert.alert_message


def test_should_create_alert_deduplication(db: Session):
    """测试告警去重逻辑"""
    # 创建第一个告警
    alert1 = Alert(
        username="testuser",
        alert_type="frequency",
        alert_message="Test",
        severity="medium",
        status="pending"
    )
    db.add(alert1)
    db.commit()
    
    # 24小时内应该不创建新告警
    should_create = should_create_alert(db, "testuser", "frequency")
    assert should_create is False
    
    # 修改状态为 resolved
    alert1.status = "resolved"
    db.commit()
    
    # 现在可以创建新告警
    should_create = should_create_alert(db, "testuser", "frequency")
    assert should_create is True
```

- [ ] **Step 2: 运行测试**

```bash
cd e:/实习/backend
$env:PYTHONPATH = "E:\实习\backend"
pytest tests/test_detection.py -v
```

Expected: 所有测试通过

- [ ] **Step 3: 提交**

```bash
cd e:/实习
git add backend/tests/test_detection.py
git commit -m "test: add detection service tests"
```

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-07-10-anomaly-detection-impl.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?