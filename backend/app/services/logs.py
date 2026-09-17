import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.login_log import LoginLog
from app.schemas.login_log import LoginLogCreate

logger = logging.getLogger(__name__)


def build_log_query(
    db: Session,
    username: Optional[str] = None,
    ip_address: Optional[str] = None,
    login_status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
):
    """构建日志查询（默认排除软删除数据）"""
    query = db.query(LoginLog).filter(LoginLog.deleted_at.is_(None))

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
    """创建日志记录并触发异步异常检测

    先落库再尝试投递检测任务：投递失败**不影响**上报结果。日志已经持久化，
    且 Celery Beat 的每小时增量扫描会兜底补检（见 docs/tech/11-性能分析.md PERF-00）。
    """
    log = LoginLog(**log_data.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)

    # 触发异步异常检测（延迟导入避免循环引用）
    from app.tasks.detection import detect_anomaly_for_log

    try:
        detect_anomaly_for_log.delay(log.id)
    except Exception:  # noqa: BLE001 — broker 不可用不应让上报接口失败
        logger.exception(
            "Failed to enqueue anomaly detection for log_id=%s; "
            "log persisted and will be covered by the hourly beat sweep",
            log.id,
        )

    return log
