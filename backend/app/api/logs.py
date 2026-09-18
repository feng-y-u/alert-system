from datetime import datetime, timezone
from typing import Type, TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.core.config import business_tz, to_utc_naive
from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_api_key
from app.models.login_log import LoginLog
from app.models.user import User
from app.schemas.login_log import LoginLogCreate, LoginLogResponse
from app.schemas.logs_query import LogQueryParams, LogListResponse
from app.services import audit
from app.services.logs import create_log, get_logs

router = APIRouter()

ModelT = TypeVar("ModelT", bound=BaseModel)


def _validated(model: Type[ModelT]):
    """把 ``Depends(<pydantic 模型>)`` 的校验失败转成 422。

    FastAPI 只对「请求体」和「单个 Query/Path 参数」把校验错误转成 422；
    以 ``Depends()`` 注入的 pydantic 模型是普通的**可调用依赖函数**，它抛出的
    ``ValidationError`` 会穿透到 Starlette 的兜底处理，最终变成 **500**。

    影响面是所有字段约束（``limit`` 上限、``skip`` 下限、``login_status`` 的
    ``pattern``、以及模型级的自定义校验），它们过去全部输出 500 而不是 422
    （见 BUG-001）。这里统一收口。

    注意必须显式把 ``request.query_params`` 传进模型：依赖函数没有参数时
    ``model()`` 会退化成「全部取默认值」，等于完全跳过校验。

    模型内自行抛出的 ``HTTPException``（如时间范围反序）原样透传，不经此处转换。
    """
    def dependency(request: Request) -> ModelT:
        try:
            return model(**dict(request.query_params))
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.errors(),
            )
    return dependency


def _require_confirmation(confirm: bool, action: str) -> None:
    """销毁类操作必须显式确认（P1-4）。"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{action}属于不可逆操作，需显式携带 confirm=true 确认",
        )


def _business_local_to_utc_naive(value: datetime | None) -> datetime | None:
    """把查询入参时间统一折算为库内的 UTC naive。

    库内 ``login_time`` 存 UTC naive，而界面上的日期范围是**用户选择的自然日**。
    直接下推会让筛选口径与展示口径错开一个时区差（默认 Asia/Shanghai 即 8 小时）：
    「筛选 9 月 16 日」实际筛的是 UTC 9 月 16 日，而列表按本地时间渲染，
    于是要么多出凌晨的记录、要么漏掉上午的记录。

    这里按 ``BUSINESS_TIMEZONE`` 解释裸时间，与 ``GET /api/stats`` 的「今日」
    口径（``business_day_start``）保持一致；已经带 offset 的值按其自身时区换算
    （``LogQueryParams._to_utc_naive`` 也已做过一次折算，这里是兜底）。
    """
    if value is None:
        return None
    if value.tzinfo is not None:
        return to_utc_naive(value)
    return to_utc_naive(value.replace(tzinfo=business_tz()))


@router.post("/logs", response_model=LoginLogResponse, status_code=201)
def receive_log(
    data: LoginLogCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """接收登录日志（校园系统调用）"""
    return create_log(db, data)


@router.get("/logs", response_model=LogListResponse)
def list_logs(
    params: LogQueryParams = Depends(_validated(LogQueryParams)),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询日志列表（管理员调用，不含软删除数据）"""
    logs, total = get_logs(
        db,
        skip=params.skip,
        limit=params.limit,
        username=params.username,
        ip_address=params.ip_address,
        login_status=params.login_status,
        start_time=_business_local_to_utc_naive(params.start_time),
        end_time=_business_local_to_utc_naive(params.end_time),
    )
    return {
        "items": logs,
        "total": total,
        "skip": params.skip,
        "limit": params.limit,
    }


@router.delete("/logs")
def clear_logs(
    confirm: bool = Query(False, description="必须显式传 true，防止误操作"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """清空登录日志（**软删除**）。

    只写 ``deleted_at`` 标记：既能立刻从所有查询与统计中消失，又保留取证可能，
    并写入审计日志（P1-4）。
    """
    _require_confirmation(confirm, "清空全部登录日志")

    now = datetime.now(timezone.utc)
    count = (
        db.query(LoginLog)
        .filter(LoginLog.deleted_at.is_(None))
        .update({LoginLog.deleted_at: now}, synchronize_session=False)
    )
    db.commit()

    audit.record(
        db,
        audit.AUDIT_LOGS_CLEARED,
        actor=current_user,
        target="login_logs",
        detail="软删除全部登录日志",
        affected_rows=count,
    )
    return {"deleted": count, "soft_deleted": True}
