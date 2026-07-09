from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.login_log import LoginLogResponse


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
