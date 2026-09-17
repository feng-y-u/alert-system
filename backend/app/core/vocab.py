"""领域词表（唯一事实来源）。

这些字段在数据库中是**裸字符串、无 CHECK 约束**：写错不会报错，但会让前端展示、
筛选与统计静默出错（见 ``docs/tech/13-开发指南.md`` §24.6、``14-评估与改进.md`` P1-3）。
所有校验与归一化都从这里取值，避免同一词表散落多处。
"""

from typing import Literal

# ── login_logs.login_status ────────────────────────────────
LOGIN_STATUS_SUCCESS = "success"
LOGIN_STATUS_FAILURE = "failure"

#: 规范取值（写库与查询都用它）
LoginStatus = Literal["success", "failure"]

#: 历史别名 → 归一化目标。``failed`` 曾由 monitored-app 上报，入库前统一为 ``failure``
LOGIN_STATUS_ALIASES = {
    "success": LOGIN_STATUS_SUCCESS,
    "failure": LOGIN_STATUS_FAILURE,
    "failed": LOGIN_STATUS_FAILURE,
    "fail": LOGIN_STATUS_FAILURE,
}

# ── alerts.alert_type ──────────────────────────────────────
ALERT_TYPE_FREQUENCY = "frequency"
ALERT_TYPE_DEVICE = "device"
AlertType = Literal["frequency", "device"]

# ── alerts.severity ────────────────────────────────────────
ALERT_SEVERITY_LOW = "low"
ALERT_SEVERITY_MEDIUM = "medium"
ALERT_SEVERITY_HIGH = "high"
AlertSeverity = Literal["low", "medium", "high"]

# ── alerts.status ──────────────────────────────────────────
ALERT_STATUS_PENDING = "pending"
ALERT_STATUS_ACKNOWLEDGED = "acknowledged"
ALERT_STATUS_RESOLVED = "resolved"
AlertStatus = Literal["pending", "acknowledged", "resolved"]

#: 「已处理」状态集合：告警去重只被 pending 阻塞，清空 scope=processed 只删这两个
PROCESSED_ALERT_STATUSES = (ALERT_STATUS_ACKNOWLEDGED, ALERT_STATUS_RESOLVED)

# ── 密码策略 ───────────────────────────────────────────────
#: 新密码最小长度（schemas 校验与 service 复检共用同一常量）
MIN_PASSWORD_LENGTH = 8
