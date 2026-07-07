from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LoginLogCreate(BaseModel):
    username: str
    login_time: datetime
    ip_address: str
    user_agent: str | None = None
    login_status: str
    location: str | None = None


class LoginLogResponse(BaseModel):
    id: int
    username: str
    login_time: datetime
    ip_address: str
    user_agent: str | None
    login_status: str
    location: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginLogQuery(BaseModel):
    """登录日志查询参数，配合 FastAPI Depends() 使用以自动解析为 URL query 参数"""
    username: str | None = None
    login_status: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    skip: int = 0
    limit: int = 50