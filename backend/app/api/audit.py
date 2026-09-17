"""审计日志查询接口（只读）。

平台自身关键操作的留痕查询入口，见 ``docs/tech/14-评估与改进.md`` P1-4、
``10-安全分析.md`` SEC-12。
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("/audit-logs")
def list_audit_logs(
    action: str | None = Query(None, description="按动作过滤，如 auth.login.failed"),
    actor: str | None = Query(None, description="按操作者用户名过滤"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询平台自身的操作审计记录（倒序）"""
    query = db.query(AuditLog)

    if action:
        query = query.filter(AuditLog.action == action)
    if actor:
        query = query.filter(AuditLog.actor_username == actor)

    total = query.count()
    rows = (
        query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    items = [
        {
            "id": row.id,
            "actor_id": row.actor_id,
            "actor_username": row.actor_username,
            "action": row.action,
            "target": row.target,
            "detail": row.detail,
            "affected_rows": row.affected_rows,
            "created_at": row.created_at,
        }
        for row in rows
    ]

    return {"items": items, "total": total, "skip": skip, "limit": limit}
