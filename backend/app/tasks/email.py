"""Celery 异步任务：邮件发送"""

import logging
import smtplib
from email.message import EmailMessage
from typing import List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.user import User
from app.tasks import celery_app

logger = logging.getLogger(__name__)


def get_active_admin_emails(db: Session) -> List[str]:
    """查询所有启用中的管理员邮箱"""
    users = db.query(User).filter(
        User.role == "admin",
        User.is_active.is_(True),
        User.email.isnot(None),
        User.email != "",
    ).all()
    return [u.email for u in users if u.email]


def is_email_configured() -> bool:
    """判断 SMTP 是否已配置真实凭据（非占位）"""
    if not settings.EMAIL_USER:
        return False
    if "example.com" in settings.EMAIL_HOST or "example" in settings.EMAIL_USER:
        return False
    return True


def build_alert_email(alert: Alert, recipients: List[str]) -> EmailMessage:
    """根据 Alert 构造告警邮件"""
    msg = EmailMessage()
    msg["From"] = settings.ALERT_EMAIL_FROM
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"[校园异常登录告警] {alert.severity.upper()} - {alert.alert_type} - 用户 {alert.username}"
    msg.set_content(
        f"检测到异常登录行为，请尽快登录平台处理。\n\n"
        f"告警ID: {alert.id}\n"
        f"告警类型: {alert.alert_type}\n"
        f"严重级别: {alert.severity}\n"
        f"用户名: {alert.username}\n"
        f"关联日志ID: {alert.log_id or '无'}\n"
        f"告警内容: {alert.alert_message}\n"
        f"创建时间: {alert.created_at}\n"
        f"状态: {alert.status}\n"
    )
    return msg


@celery_app.task(bind=True)
def send_alert_email(self, alert_id: int) -> str:
    """发送告警邮件给所有 active 管理员"""
    if not is_email_configured():
        logger.warning(
            "Email not sent for alert %s: SMTP not configured (EMAIL_USER empty or placeholder host).",
            alert_id,
        )
        return f"Email skipped (SMTP not configured) for alert {alert_id}"

    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return f"Alert {alert_id} not found"

        recipients = get_active_admin_emails(db)
        if not recipients:
            logger.warning("Email not sent for alert %s: no active admin emails.", alert_id)
            return f"Email skipped (no recipients) for alert {alert_id}"

        msg = build_alert_email(alert, recipients)

        try:
            with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USER and settings.EMAIL_PASSWORD:
                    server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
                server.send_message(msg)
        except (smtplib.SMTPException, OSError) as e:
            logger.error("SMTP send failed for alert %s: %s", alert_id, e)
            return f"Email send failed for alert {alert_id}: {e}"

        return f"Email sent to {len(recipients)} admins for alert {alert_id}"
    finally:
        db.close()