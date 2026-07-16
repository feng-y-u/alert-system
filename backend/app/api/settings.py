import smtplib
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.email import EmailConfigStatus, EmailTestResult
from app.tasks.email import get_active_admin_emails, is_email_configured

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/settings/email", response_model=EmailConfigStatus)
def get_email_config(
    current_user: User = Depends(get_current_active_user),
):
    configured = is_email_configured()
    note = ""
    if not configured:
        if not settings.EMAIL_USER:
            note = "EMAIL_USER 为空，请在 .env 中设置"
        elif "example" in settings.EMAIL_HOST or "example" in settings.EMAIL_USER:
            note = "使用了占位配置（example），请填写真实 SMTP 凭据"
    return EmailConfigStatus(
        configured=configured,
        host=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        has_user=bool(settings.EMAIL_USER),
        from_addr=settings.ALERT_EMAIL_FROM,
        note=note,
    )


@router.post("/settings/email/test", response_model=EmailTestResult)
def test_email_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if not is_email_configured():
        return EmailTestResult(success=False, message="邮件未配置，无法发送测试邮件")

    recipients = get_active_admin_emails(db)
    if not recipients:
        return EmailTestResult(success=False, message="没有活跃管理员的邮箱地址")

    try:
        with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15) as server:
            if settings.EMAIL_USER and settings.EMAIL_PASSWORD:
                server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            msg = (
                f"From: {settings.ALERT_EMAIL_FROM}\r\n"
                f"To: {', '.join(recipients)}\r\n"
                f"Subject: [校园监测平台] 邮件配置测试\r\n"
                f"\r\n"
                f"这是一封来自校园账号异常登录监测平台的测试邮件。\r\n"
                f"如果收到此邮件，说明 SMTP 配置正确。\r\n"
                f"管理员: {current_user.username}\r\n"
            )
            server.sendmail(settings.ALERT_EMAIL_FROM, recipients, msg.encode("utf-8"))

        logger.info("Test email sent successfully to %s", recipients)
        return EmailTestResult(
            success=True,
            message=f"测试邮件已发送到 {len(recipients)} 个管理员邮箱",
        )
    except smtplib.SMTPAuthenticationError:
        return EmailTestResult(success=False, message="SMTP 登录失败：账号或授权码错误")
    except smtplib.SMTPException as e:
        return EmailTestResult(success=False, message=f"SMTP 发送失败: {e}")
    except OSError as e:
        return EmailTestResult(success=False, message=f"无法连接邮件服务器: {e}")
