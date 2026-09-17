from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_api_key
from app.models.login_log import LoginLog
from app.models.user import User
from app.schemas.login_log import LoginLogCreate, LoginLogResponse
from app.schemas.logs_query import LogQueryParams, LogListResponse
from app.services import audit
from app.services.logs import create_log, get_logs

router = APIRouter()


def _require_confirmation(confirm: bool, action: str) -> None:
    """销毁类操作必须显式确认（P1-4）。"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{action}属于不可逆操作，需显式携带 confirm=true 确认",
        )


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
    params: LogQueryParams = Depends(),
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
        start_time=params.start_time,
        end_time=params.end_time,
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
