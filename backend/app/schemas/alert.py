from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertCreate(BaseModel):
    username: str
    log_id: int | None = None
    alert_type: str
    alert_message: str
    severity: str


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
    status: str


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    skip: int
    limit: int