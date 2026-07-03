"""Celery 异步任务：邮件发送"""

from app.tasks import celery_app


@celery_app.task
def send_alert_email(recipient: str, subject: str, body: str) -> str:
    """发送告警邮件（待第 5 周实现 SMTP 集成）"""
    # TODO: 第 5 周集成 SMTP 发送
    return f"Would send email to {recipient}: {subject}"