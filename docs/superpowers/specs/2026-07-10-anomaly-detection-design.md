# 第四周：异常检测模块设计

## 概述

实现登录异常检测系统，包括频率异常检测和设备异常检测。检测触发方式采用**实时检测 + 定时检测**结合。

## 检测规则

### 1. 频率异常检测

**规则：** 同一用户在 5 分钟内登录超过 10 次（滑动窗口：以最新日志时间往前推 5 分钟）

**严重级别：**
- 10-30 次/5分钟 → `medium`
- >30 次/5分钟 → `high`

**告警消息：**
- 中：用户 {username} 在 5 分钟内登录 {count} 次，可能存在异常
- 高：用户 {username} 在 5 分钟内登录 {count} 次，疑似暴力破解攻击

### 2. 设备异常检测

**规则：** 同一用户在 1 小时内 User-Agent 或 IP 地址发生变化

**严重级别：**
- 2 个不同设备/小时 → `medium`
- **≥3 个不同设备/小时 → `high`**

**告警消息：**
- 中：用户 {username} 在 1 小时内使用 2 个不同设备登录
- 高：用户 {username} 在 1 小时内使用 {count} 个不同设备登录，疑似账号共享或被盗

## 触发方式

### 实时检测（异步）
每次收到新的登录日志时，发送 Celery 异步任务进行检测

```
POST /api/logs → create_log() → detect_anomaly_for_log.delay(log_id)
```

### 定时检测（增量）
Celery Beat 每小时运行一次，**只检测上次检测后产生的新日志**

```
0 * * * *  # 每小时整点运行
```

**去重策略：** 生成告警前查询是否已存在"未处理"的同类告警（相同 username + 相同 alert_type，24小时内），避免重复告警。

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│  实时检测（API 层）                                      │
│  POST /api/logs → create_log() → Celery 异步任务       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  定时检测（Celery Beat）                                 │
│  每小时运行 → run_anomaly_detection()                   │
│  （仅检测上次检测后产生的新日志）                        │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  检测服务（services/detection.py）                       │
│  ├─ detect_frequency_anomaly(db, username, log_id)      │
│  └─ detect_device_anomaly(db, username, log_id)         │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  告警去重                                               │
│  检查 24h 内是否存在 pending 的同类告警                  │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  告警存储（models/alert.py）                             │
│  创建 Alert 记录，状态 pending，关联 log_id             │
└─────────────────────────────────────────────────────────┘
```

## 数据库变更

### alerts 表增加 log_id 字段

```python
# app/models/alert.py
log_id = Column(Integer, ForeignKey("login_logs.id"), nullable=True, index=True)
```

### 新增索引

```python
# login_logs 表
Index("idx_username_login_time", "username", "login_time")

# alerts 表  
Index("idx_username_alert_type_status", "username", "alert_type", "status")
```

## 新增文件

| 文件 | 职责 |
|------|------|
| `backend/app/services/detection.py` | 异常检测核心逻辑（频率 + 设备） |
| `backend/app/api/alerts.py` | 告警查询/更新 API |
| `backend/alembic/versions/xxx_add_log_id_to_alerts.py` | 数据库迁移：添加 log_id 字段和索引 |

## 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/tasks/detection.py` | 实现定时检测任务（增量检测 + 去重） |
| `backend/app/services/logs.py` | 添加实时检测钩子，发送 Celery 异步任务 |
| `backend/app/schemas/alert.py` | 补充 AlertCreate schema（增加 log_id） |
| `backend/app/models/alert.py` | 增加 log_id 字段和索引 |
| `backend/app/models/login_log.py` | 增加复合索引 (username, login_time) |

## API 设计

### 查询告警列表

```python
GET /api/alerts?status=pending&severity=high&skip=0&limit=50
Response: AlertListResponse(items=[{
    id: int,
    username: str,
    log_id: int,  # 关联的登录日志ID
    alert_type: str,
    alert_message: str,
    severity: str,
    status: str,
    created_at: datetime,
    # 关联的日志详情（通过 log_id 查询）
    log: {
        ip_address: str,
        user_agent: str,
        login_time: datetime
    }
}], total: int)
```

### 更新告警状态

```python
PUT /api/alerts/{alert_id}
Body: AlertUpdate
```

## Schema 设计

### AlertCreate

```python
class AlertCreate(BaseModel):
    username: str
    log_id: int          # 关联的登录日志ID
    alert_type: str      # "frequency" | "device"
    alert_message: str
    severity: str        # "low" | "medium" | "high"
```

### AlertResponse（更新）

```python
class AlertResponse(BaseModel):
    id: int
    username: str
    log_id: int | None   # 新增：关联的登录日志ID
    # ... 其他字段不变
```

## Celery 任务设计

### 实时检测任务

```python
# app/tasks/detection.py
@celery_app.task
def detect_anomaly_for_log(log_id: int):
    """实时检测单条日志"""
    db = SessionLocal()
    try:
        log = db.query(LoginLog).filter(LoginLog.id == log_id).first()
        if not log:
            return
        
        # 频率检测
        detect_frequency_anomaly(db, log.username, log_id)
        
        # 设备检测
        detect_device_anomaly(db, log.username, log_id)
    finally:
        db.close()
```

### 定时检测任务

```python
@celery_app.task
def run_anomaly_detection():
    """每小时运行增量异常检测"""
    db = SessionLocal()
    try:
        # 获取上次检测时间（从 Redis 或数据库记录）
        last_check_time = get_last_check_time()
        
        # 获取上次检测后产生日志的所有用户
        users = get_users_with_new_logs(db, last_check_time)
        
        for username in users:
            # 频率检测
            detect_frequency_anomaly(db, username, log_id=None, since=last_check_time)
            
            # 设备检测
            detect_device_anomaly(db, username, log_id=None, since=last_check_time)
        
        # 更新上次检测时间
        set_last_check_time(datetime.utcnow())
    finally:
        db.close()
```

## 检测服务接口

```python
# app/services/detection.py

def detect_frequency_anomaly(
    db: Session, 
    username: str, 
    log_id: int | None = None,
    since: datetime | None = None
) -> Alert | None:
    """
    检测频率异常
    - log_id: 实时检测时传入，用于定位当前日志
    - since: 定时检测时传入，用于增量检测
    """
    pass

def detect_device_anomaly(
    db: Session, 
    username: str, 
    log_id: int | None = None,
    since: datetime | None = None
) -> Alert | None:
    """
    检测设备异常
    """
    pass

def should_create_alert(
    db: Session,
    username: str,
    alert_type: str
) -> bool:
    """
    检查是否应该创建新告警（去重逻辑）
    24小时内是否存在 pending 的同类告警
    """
    pass
```

## 非目标

- 不实现地理位置检测（IP 库）— 第 8 周后扩展
- 不实现告警规则配置界面 — 第 7 周
- 不实现邮件通知 — 第 5 周
- 不修改前端 — 第 6 周统一联调

## 成功标准

1. **实时检测：** 新登录日志产生后，Celery 任务在 5 秒内完成检测
2. **定时检测：** 每小时运行，只处理增量数据，不重复检测旧日志
3. **告警去重：** 同一用户、同一异常类型，24 小时内只生成一条 pending 告警
4. **告警关联：** 可以通过 log_id 查询到触发告警的具体登录日志详情
5. **API 可用：** 可以通过 `/api/alerts` 查询和更新告警，返回包含日志详情