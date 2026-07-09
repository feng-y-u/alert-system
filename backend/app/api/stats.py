from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
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