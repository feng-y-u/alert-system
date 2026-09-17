from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.vocab import LOGIN_STATUS_ALIASES, LoginStatus


class LoginLogCreate(BaseModel):
    username: str
    login_time: datetime
    ip_address: str
    user_agent: str | None = None
    login_status: str
    location: str | None = None

    @field_validator("login_status")
    @classmethod
    def _normalize_login_status(cls, value: str) -> str:
        """统一 ``login_status`` 词表：``failed``/``fail`` → ``failure``。

        历史上报方（monitored-app）写的是 ``failed``，而查询与前端一律用
        ``failure``，曾导致「数据能入库但按失败筛不出来」。此处入库即归一化，
        不再依赖调用方自觉（见 docs/tech/14-评估与改进.md P1-3）。
        """
        normalized = LOGIN_STATUS_ALIASES.get((value or "").strip().lower())
        if normalized is None:
            raise ValueError(
                f"login_status 取值非法：{value!r}；允许 success / failure（failed 会被归一化为 failure）"
            )
        return normalized


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
    """登录日志查询参数（历史遗留模型，实际查询用 schemas/logs_query.LogQueryParams）"""
    username: str | None = None
    login_status: LoginStatus | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    skip: int = 0
    limit: int = 50
