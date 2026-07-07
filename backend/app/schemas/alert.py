from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: int
    username: str
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