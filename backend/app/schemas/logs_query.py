from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.login_log import LoginLogResponse


class LogQueryParams(BaseModel):
    """日志查询参数。

    该模型以 ``Depends()`` 注入（不是请求体），因此 Pydantic 抛出的
    ``ValueError`` **不会**被 FastAPI 转成 422，而会穿透成 500。
    所以校验失败一律抛 ``HTTPException``。
    """
    username: Optional[str] = Field(None, description="模糊匹配用户名")
    ip_address: Optional[str] = None
    login_status: Optional[str] = Field(None, pattern="^(success|failure)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)

    @field_validator("start_time", "end_time", mode="after")
    @classmethod
    def _to_utc_naive(cls, value: Optional[datetime]) -> Optional[datetime]:
        """把带时区的入参统一折算为 UTC naive。

        库内 ``login_time`` 存的是 UTC naive，查询参数必须用同一口径比较。
        不折算会有两个后果：

        1. 一个带 offset、一个不带时，下面的 ``start_time > end_time``
           会抛 ``TypeError: can't compare offset-naive and offset-aware datetimes``。
           Pydantic 只把 ``ValueError`` 转成校验错误，``TypeError`` 会穿透到
           FastAPI 依赖解析，最终返回 **500**（而不是 422）。
        2. 带 offset 的值直接下推数据库时，MySQL 会**静默剥离 tzinfo**，
           造成一个时区差的偏移。

        注意必须是 ``mode="after"``：``mode="before"`` 拿到的是原始字符串，
        类型判断会失效（``isinstance("...+08:00", datetime)`` 恒为 False），
        折算就被静默跳过。
        """
        if value is not None and value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    @model_validator(mode='after')
    def check_time_range(self):
        """校验时间范围。

        抛 ``HTTPException(422)`` 而不是 ``ValueError``：查询参数模型由
        ``Depends()`` 注入，``ValueError`` 在这里只会变成 500
        （见 BUG-001 —— 参数非法必须返回 4xx，而不是服务端错误）。
        """
        if self.start_time and self.end_time and self.start_time > self.end_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_time 不能晚于 end_time",
            )
        return self


class LogListResponse(BaseModel):
    """日志列表响应"""
    items: list[LoginLogResponse]
    total: int
    skip: int
    limit: int
