"""Celery 异步任务：异常检测"""

from datetime import datetime, timedelta

import redis

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.login_log import LoginLog
from app.services.detection import detect_device_anomaly, detect_frequency_anomaly
from app.tasks import celery_app

# Redis 客户端用于存储上次检测时间
redis_client = redis.from_url(settings.REDIS_URL)

LAST_CHECK_KEY = "anomaly_detection:last_check_time"


def get_last_check_time() -> datetime:
    """获取上次检测时间"""
    last_check = redis_client.get(LAST_CHECK_KEY)
    if last_check:
        return datetime.fromisoformat(last_check.decode())
    # 默认返回1小时前
    return datetime.utcnow() - timedelta(hours=1)


def set_last_check_time(time: datetime):
    """设置上次检测时间"""
    redis_client.set(LAST_CHECK_KEY, time.isoformat())


@celery_app.task
def detect_anomaly_for_log(log_id: int) -> str:
    """
    实时检测单条日志的异常

    Args:
        log_id: 登录日志ID

    Returns:
        检测结果的描述字符串
    """
    db = SessionLocal()
    try:
        log = db.query(LoginLog).filter(LoginLog.id == log_id).first()
        if not log:
            return f"Log {log_id} not found"

        results = []

        # 频率检测
        freq_alert = detect_frequency_anomaly(db, log.username, log_id)
        if freq_alert:
            results.append(f"Frequency alert created: {freq_alert.id}")

        # 设备检测
        device_alert = detect_device_anomaly(db, log.username, log_id)
        if device_alert:
            results.append(f"Device alert created: {device_alert.id}")

        if results:
            return "; ".join(results)
        return "No anomaly detected"

    except Exception as e:
        return f"Error during detection: {str(e)}"

    finally:
        db.close()


@celery_app.task
def run_anomaly_detection() -> str:
    """
    每小时运行增量异常检测

    只检测上次检测后产生的新日志

    Returns:
        检测结果的描述字符串
    """
    db = SessionLocal()
    try:
        # 获取上次检测时间
        last_check_time = get_last_check_time()
        current_time = datetime.utcnow()

        # 获取上次检测后产生日志的所有用户
        users = db.query(LoginLog.username).filter(
            LoginLog.created_at >= last_check_time
        ).distinct().all()

        users = [u[0] for u in users]

        total_alerts = 0

        for username in users:
            # 频率检测
            freq_alert = detect_frequency_anomaly(
                db, username, log_id=None, since=last_check_time
            )
            if freq_alert:
                total_alerts += 1

            # 设备检测
            device_alert = detect_device_anomaly(
                db, username, log_id=None, since=last_check_time
            )
            if device_alert:
                total_alerts += 1

        # 更新上次检测时间
        set_last_check_time(current_time)

        return f"Anomaly detection completed. Checked {len(users)} users, created {total_alerts} alerts."

    except Exception as e:
        return f"Error during anomaly detection: {str(e)}"

    finally:
        db.close()