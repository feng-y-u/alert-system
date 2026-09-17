"""审计日志写入（平台自身的操作留痕）。

约定：

- 审计写入失败**不得影响业务操作**，因此异常只记录不抛出；
- ``detail`` 中**禁止**写入口令、token、授权码等敏感信息；
- 动作标识集中在本模块定义，避免各处拼写漂移。

见 ``docs/tech/14-评估与改进.md`` P1-4、``10-安全分析.md`` SEC-12。
"""

import logging

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

# ── 动作标识（唯一事实来源）────────────────────────────────
AUDIT_LOGIN_SUCCESS = "auth.login.success"
AUDIT_LOGIN_FAILED = "auth.login.failed"
AUDIT_USER_CREATED = "auth.user.created"
AUDIT_PASSWORD_CHANGED = "auth.password.changed"
AUDIT_LOGS_CLEARED = "logs.cleared"
AUDIT_ALERTS_CLEARED = "alerts.cleared"
AUDIT_ALERT_STATUS_CHANGED = "alert.status.changed"


def record(
    db: Session,
    action: str,
    actor=None,
    target: str | None = None,
    detail: str | None = None,
    affected_rows: int | None = None,
    commit: bool = True,
) -> AuditLog | None:
    """写入一条审计记录。

    Args:
        db: 会话
        action: 动作标识（用本模块常量）
        actor: 操作者 User 对象；未登录场景传 ``None``
        target: 作用对象
        detail: 说明（不含敏感信息）
        affected_rows: 受影响行数
        commit: 是否立即提交（调用方已提交业务改动时保持 True 即可）

    Returns:
        写入的 :class:`AuditLog`；写入失败返回 ``None``。
    """
    try:
        entry = AuditLog(
            actor_id=getattr(actor, "id", None),
            actor_username=getattr(actor, "username", None),
            action=action,
            target=target,
            detail=(detail[:500] if detail else None),
            affected_rows=affected_rows,
        )
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        return entry
    except Exception:
        logger.exception("写审计日志失败：action=%s target=%s", action, target)
        try:
            db.rollback()
        except Exception:  # pragma: no cover - 回滚失败无需再报
            pass
        return None
