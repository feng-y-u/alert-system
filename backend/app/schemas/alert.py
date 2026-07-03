from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AlertResponse(BaseModel):
    id: int
    user_id: int
    alert_type: str
    alert_message: str
    severity: str
    status: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertUpdate(BaseModel):
    status: str