"""Celery 异步任务：异常检测。

健壮性约定（对应 docs/tech/14-评估与改进.md P1-5）：

- 异常不再被吞成返回字符串：``logger.exception`` 留痕 + ``self.retry`` 有限重试，
  失败会以 FAILURE 状态体现在 worker 日志中；
- 定时检测的**游标在处理成功后才推进**：失败时保留原游标，下一轮会重新覆盖该窗口，
  避免「先推进游标 + 异常」导致的时间窗永久漏检。
"""

import json
import logging
from datetime import datetime, timedelta, timezone

import redis

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.login_log import LoginLog
from app.services.detection import detect_device_anomaly, detect_frequency_anomaly
from app.tasks import celery_app
from app.tasks.email import send_alert_email

logger = logging.getLogger(__name__)


def _publish_alert_event(alert):
    """发布告警事件到 Redis pub/sub（失败不影响告警生成主流程）"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.publish("alerts", json.dumps({
            "alert_id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "username": alert.username,
        }))
    except Exception:
        logger.warning("发布告警事件到 Redis 失败：alert_id=%s", getattr(alert, "id", None), exc_info=True)


def _dispatch_alert_side_effects(alert) -> None:
    """投递邮件 + 发布实时事件；单条失败不应让整个检测任务重试。"""
    try:
        send_alert_email.delay(alert.id)
    except Exception:
        logger.exception("投递告警邮件任务失败：alert_id=%s", alert.id)
    _publish_alert_event(alert)


# Redis 客户端用于存储上次检测时间
redis_client = redis.from_url(settings.REDIS_URL)

LAST_CHECK_KEY = "anomaly_detection:last_check_time"


def get_last_check_time() -> datetime:
    """获取上次检测时间"""
    last_check = redis_client.get(LAST_CHECK_KEY)
    if last_check:
        return datetime.fromisoformat(last_check.decode())
    # 默认返回1小时前
    return datetime.now(timezone.utc) - timedelta(hours=1)


def set_last_check_time(time: datetime):
    """设置上次检测时间"""
    redis_client.set(LAST_CHECK_KEY, time.isoformat())


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def detect_anomaly_for_log(self, log_id: int) -> str:
    """
    实时检测单条日志的异常

    Args:
        log_id: 登录日志ID

    Returns:
        检测结果的描述字符串

    Raises:
        Retry: 内部错误时按 max_retries 有限重试，耗尽后抛出原始异常
    """
    db = SessionLocal()
    try:
        log = db.query(LoginLog).filter(LoginLog.id == log_id).first()
        if not log:
            logger.warning("实时检测跳过：日志不存在 log_id=%s", log_id)
            return f"Log {log_id} not found"

        results = []

        # 频率检测
        freq_alert = detect_frequency_anomaly(db, log.username, log_id)
        if freq_alert:
            results.append(f"Frequency alert created: {freq_alert.id}")
            _dispatch_alert_side_effects(freq_alert)

        # 设备检测
        device_alert = detect_device_anomaly(db, log.username, log_id)
        if device_alert:
            results.append(f"Device alert created: {device_alert.id}")
            _dispatch_alert_side_effects(device_alert)

        if results:
            outcome = "; ".join(results)
        else:
            outcome = "No anomaly detected"
        logger.info("实时检测完成 log_id=%s：%s", log_id, outcome)
        return outcome

    except Exception as exc:
        logger.exception("实时检测失败 log_id=%s，将重试（最多 %s 次）", log_id, self.max_retries)
        raise self.retry(exc=exc)

    finally:
        db.close()


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def run_anomaly_detection(self) -> str:
    """
    每小时运行增量异常检测

    只检测上次检测后产生的新日志。游标在**全部处理成功后**才推进。

    Returns:
        检测结果的描述字符串
    """
    db = SessionLocal()
    try:
        # 获取上次检测时间（失败时保持不变，下一轮重新覆盖该窗口）
        last_check_time = get_last_check_time()

        # 获取上次检测后产生日志的所有用户（排除软删除）
        users = db.query(LoginLog.username).filter(
            LoginLog.created_at >= last_check_time,
            LoginLog.deleted_at.is_(None),
        ).distinct().all()

        users = [u[0] for u in users]

        total_alerts = 0

        for username in users:
            # 频率检测
            freq_alert = detect_frequency_anomaly(db, username)
            if freq_alert:
                total_alerts += 1
                _dispatch_alert_side_effects(freq_alert)

            # 设备检测
            device_alert = detect_device_anomaly(db, username)
            if device_alert:
                total_alerts += 1
                _dispatch_alert_side_effects(device_alert)

        # 处理成功后才推进游标
        set_last_check_time(datetime.now(timezone.utc))

        summary = (
            f"Anomaly detection completed. Checked {len(users)} users, "
            f"created {total_alerts} alerts."
        )
        logger.info(summary)
        return summary

    except Exception as exc:
        logger.exception("定时检测失败，检测游标保持不变，下一轮将重新覆盖该窗口")
        raise self.retry(exc=exc)

    finally:
        db.close()
