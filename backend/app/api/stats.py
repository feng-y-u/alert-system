from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.models.login_log import LoginLog
from app.models.alert import Alert

router = APIRouter()


@router.get("/stats")
def get_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取仪表盘统计数据"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 今日登录次数
    today_logins = db.query(LoginLog).filter(
        LoginLog.login_time >= today_start
    ).count()

    # 待处理告警数
    pending_alerts = db.query(Alert).filter(
        Alert.status == "pending"
    ).count()

    # 活跃用户数（今日有登录记录的用户）
    active_users = db.query(LoginLog.username).filter(
        LoginLog.login_time >= today_start
    ).distinct().count()

    # 登录趋势（支持近7天或近30天）
    trend = []
    for i in range(days - 1, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.query(LoginLog).filter(
            LoginLog.login_time >= day_start,
            LoginLog.login_time < day_end,
        ).count()
        trend.append({
            "date": day_start.strftime("%m-%d"),
            "count": count,
        })

    return {
        "todayLogins": today_logins,
        "pendingAlerts": pending_alerts,
        "activeUsers": active_users,
        "loginTrend": trend,
    }


@router.get("/stats/alerts")
def get_alert_stats(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取告警维度统计数据（趋势/类型分布/级别分布）"""
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(days=days)

    # 告警趋势：逐日统计
    trend = []
    for i in range(days - 1, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.query(Alert).filter(
            Alert.created_at >= day_start,
            Alert.created_at < day_end,
        ).count()
        trend.append({
            "date": day_start.strftime("%m-%d"),
            "count": count,
        })

    # 类型分布
    type_rows = db.query(Alert.alert_type, func.count()).filter(
        Alert.created_at >= window_start,
    ).group_by(Alert.alert_type).all()
    type_dist = [{"name": t, "value": c} for t, c in type_rows]

    # 级别分布
    severity_rows = db.query(Alert.severity, func.count()).filter(
        Alert.created_at >= window_start,
    ).group_by(Alert.severity).all()
    severity_dist = [{"name": s, "value": c} for s, c in severity_rows]

    return {
        "alertTrend": trend,
        "typeDist": type_dist,
        "severityDist": severity_dist,
    }