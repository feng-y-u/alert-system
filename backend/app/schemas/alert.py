from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.vocab import AlertSeverity, AlertStatus, AlertType


class AlertCreate(BaseModel):
    username: str
    log_id: int | None = None
    alert_type: AlertType
    alert_message: str
    severity: AlertSeverity


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


class AlertUpdate(BaseModel):
    """告警状态变更。

    ``status`` 使用 ``Literal`` 约束：此前是自由字符串，写错也会入库，
    前端只能原样展示未知状态（见 docs/tech/14-评估与改进.md P1-3）。
    """

    status: AlertStatus


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    skip: int
    limit: int
