from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate


def build_log_query(
    db: Session,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    login_status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """构建日志查询"""
    query = db.query(LoginLog)

    if username:
        query = query.filter(LoginLog.username.contains(username))
    if ip_address:
        query = query.filter(LoginLog.ip_address == ip_address)
    if login_status:
        query = query.filter(LoginLog.login_status == login_status)
    if start_time:
        query = query.filter(LoginLog.login_time >= start_time)
    if end_time:
        query = query.filter(LoginLog.login_time <= end_time)

    return query.order_by(desc(LoginLog.login_time))


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    **filters
) -> tuple[list[LoginLog], int]:
    """获取日志列表和总数"""
    query = build_log_query(db, **filters)
    total = query.count()
    logs = query.offset(skip).limit(limit).all()
    return logs, total


def create_log(db: Session, log_data: LoginLogCreate) -> LoginLog:
    """创建日志记录"""
    log = LoginLog(**log_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
