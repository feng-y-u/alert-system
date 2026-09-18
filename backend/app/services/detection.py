"""异常检测服务"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.login_log import LoginLog
from app.schemas.alert import AlertCreate

logger = logging.getLogger(__name__)


def _create_alert_once(db: Session, alert_data: AlertCreate) -> Optional[Alert]:
    """并发安全地创建告警。

    ``should_create_alert`` 的 SELECT 与 INSERT 之间存在窗口：两条并发日志各自
    投递一次检测任务，两个任务可能都查到「没有 pending 告警」，于是各插一条，
    去重承诺失效（还会重复发邮件、重复推 SSE）。

    这里由数据库的唯一索引 ``uq_alerts_pending_dedup`` 兜底：第二条 INSERT 会被
    拒绝，``IntegrityError`` 说明**去重生效**而不是出错，因此回滚后返回 None，
    让调用方跳过告警副作用。

    Returns:
        新建的 Alert；若被并发去重拦下则返回 None。
    """
    alert = Alert(**alert_data.model_dump())
    db.add(alert)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        logger.info(
            "并发去重生效，跳过重复告警：username=%s alert_type=%s",
            alert_data.username,
            alert_data.alert_type,
        )
        return None
    db.refresh(alert)
    return alert


def detect_frequency_anomaly(
    db: Session,
    username: str,
    log_id: Optional[int] = None
) -> Optional[Alert]:
    """
    检测频率异常：同一用户5分钟内登录超过10次

    Args:
        db: 数据库会话
        username: 用户名
        log_id: 实时检测时传入，用于定位当前日志

    Returns:
        如果检测到异常返回 Alert，否则返回 None
    """
    # 确定时间窗口
    if log_id:
        # 实时检测：获取当前日志时间（软删除的日志不参与检测）
        current_log = (
            db.query(LoginLog)
            .filter(LoginLog.id == log_id, LoginLog.deleted_at.is_(None))
            .first()
        )
        if not current_log:
            return None
        end_time = current_log.login_time
    else:
        # 定时检测：使用当前时间
        end_time = datetime.now(timezone.utc)

    start_time = end_time - timedelta(minutes=5)

    # 查询时间窗口内的登录次数
    count = db.query(func.count(LoginLog.id)).filter(
        LoginLog.username == username,
        LoginLog.login_time >= start_time,
        LoginLog.login_time <= end_time,
        LoginLog.deleted_at.is_(None),
    ).scalar()

    # 判断是否异常
    if count < 10:
        return None

    # 确定严重级别
    if count <= 30:
        severity = "medium"
        message = f"用户 {username} 在5分钟内登录 {count} 次，可能存在异常"
    else:
        severity = "high"
        message = f"用户 {username} 在5分钟内登录 {count} 次，疑似暴力破解攻击"

    # 检查是否应该创建告警（去重）
    # 这里只是「便宜的前置过滤」，真正的不变量由 _create_alert_once 的唯一索引保证
    if not should_create_alert(db, username, "frequency"):
        return None

    # 创建告警
    return _create_alert_once(
        db,
        AlertCreate(
            username=username,
            log_id=log_id,
            alert_type="frequency",
            alert_message=message,
            severity=severity,
        ),
    )


def detect_device_anomaly(
    db: Session,
    username: str,
    log_id: Optional[int] = None
) -> Optional[Alert]:
    """
    检测设备异常：同一用户1小时内User-Agent或IP发生变化

    Args:
        db: 数据库会话
        username: 用户名
        log_id: 实时检测时传入

    Returns:
        如果检测到异常返回 Alert，否则返回 None
    """
    # 确定时间窗口
    if log_id:
        current_log = (
            db.query(LoginLog)
            .filter(LoginLog.id == log_id, LoginLog.deleted_at.is_(None))
            .first()
        )
        if not current_log:
            return None
        end_time = current_log.login_time
    else:
        end_time = datetime.now(timezone.utc)

    start_time = end_time - timedelta(hours=1)

    # 查询时间窗口内的不同设备数（按user_agent + ip_address组合）
    rows = db.query(LoginLog.user_agent, LoginLog.ip_address).filter(
        LoginLog.username == username,
        LoginLog.login_time >= start_time,
        LoginLog.login_time <= end_time,
        LoginLog.deleted_at.is_(None),
    ).distinct().all()

    device_count = len(rows)

    # 判断是否异常（2个及以上设备）
    if device_count < 2:
        return None

    # 确定严重级别
    if device_count == 2:
        severity = "medium"
        message = f"用户 {username} 在1小时内使用2个不同设备登录"
    else:
        severity = "high"
        message = f"用户 {username} 在1小时内使用 {device_count} 个不同设备登录，疑似账号共享或被盗"

    # 检查是否应该创建告警（去重）
    # 这里只是「便宜的前置过滤」，真正的不变量由 _create_alert_once 的唯一索引保证
    if not should_create_alert(db, username, "device"):
        return None

    # 创建告警
    return _create_alert_once(
        db,
        AlertCreate(
            username=username,
            log_id=log_id,
            alert_type="device",
            alert_message=message,
            severity=severity,
        ),
    )


def should_create_alert(
    db: Session,
    username: str,
    alert_type: str
) -> bool:
    """
    检查是否应该创建新告警（去重逻辑）

    24小时内是否存在 pending 的同类告警

    Args:
        db: 数据库会话
        username: 用户名
        alert_type: 告警类型

    Returns:
        True 表示应该创建新告警，False 表示已存在未处理的同类告警
    """
    since = datetime.now(timezone.utc) - timedelta(hours=24)

    existing = db.query(Alert).filter(
        Alert.username == username,
        Alert.alert_type == alert_type,
        Alert.status == "pending",
        Alert.created_at >= since,
        Alert.deleted_at.is_(None),
    ).first()

    return existing is None
