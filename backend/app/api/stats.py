"""统计接口。

时间口径（P1-8 统一后）：数据库统一存 **UTC naive**；对外展示的「今日/趋势」
按 ``settings.BUSINESS_TIMEZONE`` 的自然日切分，Celery 调度使用同一时区。

过滤口径（P1-4）：统计一律排除软删除数据（``deleted_at IS NULL``）。

性能（P1-1）：趋势统计由「逐日 N 次 COUNT」改为**单条 GROUP BY 查询**，
并为 ``days`` 增加范围校验，消除 ``?days=100000`` 造成的资源耗尽面。
"""

from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.config import (
    business_day_start,
    business_day_start_utc_naive,
    business_utc_offset_hours,
    to_utc_naive,
)
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.login_log import LoginLog
from app.models.alert import Alert

router = APIRouter()

DAYS_MIN = 1
DAYS_MAX = 365


def _not_deleted(model):
    """软删除过滤条件。"""
    return model.deleted_at.is_(None)


def _business_date_expr(db: Session, column):
    """把 UTC naive 时间列折算为「业务时区自然日」，跨 SQLite / MySQL 可移植。"""
    offset = business_utc_offset_hours()
    dialect = db.get_bind().dialect.name
    if dialect == "sqlite":
        return func.date(column, f"+{offset} hours")
    # MySQL / MariaDB
    return func.date(func.date_add(column, text(f"INTERVAL {offset} HOUR")))


def _daily_counts(db: Session, column, start, end, model) -> dict:
    """单条查询取回 [start, end) 内按业务自然日分组的计数（排除软删除）。"""
    expr = _business_date_expr(db, column)
    rows = (
        db.query(expr.label("business_day"), func.count())
        .filter(column >= start, column < end, _not_deleted(model))
        .group_by(expr)
        .all()
    )
    return {str(day): int(count) for day, count in rows}


def _build_trend(db: Session, column, days: int, model) -> List[dict]:
    """最近 ``days`` 天的趋势序列（无数据的日期补 0）。"""
    today_start = business_day_start()
    first_day_start = today_start - timedelta(days=days - 1)

    counts = _daily_counts(
        db,
        column,
        to_utc_naive(first_day_start),
        to_utc_naive(today_start + timedelta(days=1)),
        model,
    )

    trend: List[dict] = []
    for i in range(days):
        day = first_day_start + timedelta(days=i)
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "count": counts.get(day.strftime("%Y-%m-%d"), 0),
            }
        )
    return trend


@router.get("/stats")
def get_stats(
    days: int = Query(7, ge=DAYS_MIN, le=DAYS_MAX, description="趋势天数（1-365）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取仪表盘统计数据"""
    today_start_utc = business_day_start_utc_naive()

    # 今日登录次数
    today_logins = db.query(LoginLog).filter(
        LoginLog.login_time >= today_start_utc,
        _not_deleted(LoginLog),
    ).count()

    # 待处理告警数
    pending_alerts = db.query(Alert).filter(
        Alert.status == "pending",
        _not_deleted(Alert),
    ).count()

    # 活跃用户数（今日有登录记录的用户）
    active_users = (
        db.query(LoginLog.username)
        .filter(LoginLog.login_time >= today_start_utc, _not_deleted(LoginLog))
        .distinct()
        .count()
    )

    return {
        "todayLogins": today_logins,
        "pendingAlerts": pending_alerts,
        "activeUsers": active_users,
        "loginTrend": _build_trend(db, LoginLog.login_time, days, LoginLog),
    }


@router.get("/stats/alerts")
def get_alert_stats(
    days: int = Query(7, ge=DAYS_MIN, le=DAYS_MAX, description="统计天数（1-365）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取告警维度统计数据（趋势/类型分布/级别分布）"""
    window_start = to_utc_naive(business_day_start() - timedelta(days=days - 1))

    # 类型分布
    type_rows = (
        db.query(Alert.alert_type, func.count())
        .filter(Alert.created_at >= window_start, _not_deleted(Alert))
        .group_by(Alert.alert_type)
        .all()
    )
    type_dist = [{"name": t, "value": c} for t, c in type_rows]

    # 级别分布
    severity_rows = (
        db.query(Alert.severity, func.count())
        .filter(Alert.created_at >= window_start, _not_deleted(Alert))
        .group_by(Alert.severity)
        .all()
    )
    severity_dist = [{"name": s, "value": c} for s, c in severity_rows]

    return {
        "alertTrend": _build_trend(db, Alert.created_at, days, Alert),
        "typeDist": type_dist,
        "severityDist": severity_dist,
    }
