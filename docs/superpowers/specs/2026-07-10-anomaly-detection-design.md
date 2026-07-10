# 第四周：异常检测模块设计

## 概述

实现登录异常检测系统，包括频率异常检测和设备异常检测。检测触发方式采用**实时检测 + 定时检测**结合。

## 检测规则

### 1. 频率异常检测

**规则：** 同一用户在 5 分钟内登录超过 10 次

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
- >2 个不同设备/小时 → `high`

**告警消息：**
- 中：用户 {username} 在 1 小时内使用 {count} 个不同设备登录
- 高：用户 {username} 在 1 小时内使用 {count} 个不同设备登录，疑似账号共享或被盗

## 触发方式

### 实时检测
每次收到新的登录日志时立即触发检测

```
POST /api/logs → create_log() → trigger_detection(username)
```

### 定时检测
Celery Beat 每小时运行一次全量检测

```
0 * * * *  # 每小时整点运行
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│  实时检测（API 层）                                      │
│  POST /api/logs → create_log() → trigger_detection()   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  定时检测（Celery Beat）                                 │
│  每小时运行 → run_anomaly_detection()                   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  检测服务（services/detection.py）                       │
│  ├─ detect_frequency_anomaly(db, username)              │
│  └─ detect_device_anomaly(db, username)                 │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│  告警存储（models/alert.py）                             │
│  创建 Alert 记录，状态 pending                            │
└─────────────────────────────────────────────────────────┘
```

## 新增文件

| 文件 | 职责 |
|------|------|
| `backend/app/services/detection.py` | 异常检测核心逻辑（频率 + 设备） |
| `backend/app/api/alerts.py` | 告警查询/更新 API |

## 修改文件

| 文件 | 改动 |
|------|------|
| `backend/app/tasks/detection.py` | 实现定时检测任务，调用 services/detection.py |
| `backend/app/services/logs.py` | 添加实时检测钩子，在 create_log 后触发 |
| `backend/app/schemas/alert.py` | 补充 AlertCreate schema |

## API 设计

### 创建告警（内部调用）

```python
POST /api/alerts  # 内部使用，不对外暴露
```

### 查询告警列表

```python
GET /api/alerts?status=pending&severity=high&skip=0&limit=50
Response: AlertListResponse
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
    alert_type: str  # "frequency" | "device"
    alert_message: str
    severity: str    # "low" | "medium" | "high"
```

## Celery Beat 配置

```python
# app/tasks/detection.py
@celery_app.task
def run_anomaly_detection():
    """每小时运行全量异常检测"""
    # 获取过去 1 小时内有登录记录的所有用户
    # 对每个用户调用 detect_frequency_anomaly 和 detect_device_anomaly
    pass
```

## 非目标

- 不实现地理位置检测（IP 库）— 第 8 周后扩展
- 不实现告警规则配置界面 — 第 7 周
- 不实现邮件通知 — 第 5 周
- 不修改前端 — 第 6 周统一联调

## 成功标准

1. 实时检测：新登录日志产生后 1 秒内完成检测
2. 定时检测：每小时运行，处理过去 1 小时的所有日志
3. 告警生成：检测到异常后自动创建 Alert 记录
4. API 可用：可以通过 `/api/alerts` 查询和更新告警