from datetime import datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.vocab import LOGIN_STATUS_ALIASES, LoginStatus

#: login_time 允许的最大时钟超前量。
#: 容忍上游主机时钟偏差，但拒绝任意未来时间 —— 实时检测以该条日志自己的
#: login_time 为窗口终点，不加限制时上游可以提交未来时间干扰检测窗口。
MAX_CLOCK_SKEW = timedelta(minutes=5)


class LoginLogCreate(BaseModel):
    username: str
    login_time: datetime
    ip_address: str
    user_agent: str | None = None
    login_status: str
    location: str | None = None

    @field_validator("login_time")
    @classmethod
    def _normalize_login_time(cls, value: datetime) -> datetime:
        """统一为 UTC naive 并拒绝明显超前的未来时间。

        - 带 offset 的值先折算为 UTC naive：库内 ``login_time`` 是 UTC naive，
          而 MySQL 对 aware datetime 会**静默剥离 tzinfo**（不报错但语义偏移）；
        - 超前当前时间超过 ``MAX_CLOCK_SKEW`` 的值直接拒绝（见 BUG-008）。
        """
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        if value > now_utc_naive + MAX_CLOCK_SKEW:
            raise ValueError(
                "login_time 不得晚于当前时间（允许 "
                f"{int(MAX_CLOCK_SKEW.total_seconds() // 60)} 分钟时钟偏差）"
            )
        return value

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
