from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, verify_api_key
from app.models.user import User
from app.schemas.login_log import LoginLogCreate, LoginLogResponse
from app.schemas.logs_query import LogQueryParams, LogListResponse
from app.services.logs import create_log, get_logs

router = APIRouter()


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
    """查询日志列表（管理员调用）"""
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