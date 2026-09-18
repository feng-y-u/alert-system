from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.vocab import (
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_PENDING,
    ALERT_STATUS_RESOLVED,
    PROCESSED_ALERT_STATUSES,
    AlertSeverity,
    AlertStatus,
)
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertResponse, AlertUpdate
from app.services import audit

router = APIRouter()


def _require_confirmation(confirm: bool, action: str) -> None:
    """销毁类操作必须显式确认（P1-4）。"""
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{action}属于不可逆操作，需显式携带 confirm=true 确认",
        )


def _active_alerts(db: Session):
    """未被软删除的告警查询（所有读路径都必须经此过滤）。"""
    return db.query(Alert).filter(Alert.deleted_at.is_(None))


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    status_filter: AlertStatus | None = Query(
        None, alias="status", description="Filter by status: pending/acknowledged/resolved"
    ),
    severity: AlertSeverity | None = Query(
        None, description="Filter by severity: low/medium/high"
    ),
    username: str | None = Query(None, description="Filter by username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询告警列表（不含软删除数据）"""
    query = _active_alerts(db)

    if status_filter:
        query = query.filter(Alert.status == status_filter)
    if severity:
        query = query.filter(Alert.severity == severity)
    if username:
        query = query.filter(Alert.username == username)

    total = query.count()
    alerts = (
        query.order_by(Alert.created_at.desc(), Alert.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "items": alerts,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个告警详情"""
    alert = _active_alerts(db).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


#: 允许的告警状态转换。
#: ``resolved`` 视为闭环终态：重新打开必须先回到 ``acknowledged``，
#: 避免管理员误点下拉菜单就把已处理告警一步打回待处理。
ALLOWED_ALERT_TRANSITIONS = {
    ALERT_STATUS_PENDING: {ALERT_STATUS_ACKNOWLEDGED, ALERT_STATUS_RESOLVED},
    ALERT_STATUS_ACKNOWLEDGED: {ALERT_STATUS_PENDING, ALERT_STATUS_RESOLVED},
    ALERT_STATUS_RESOLVED: {ALERT_STATUS_ACKNOWLEDGED},
}


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    update_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新告警状态。

    - ``status`` 由 ``Literal`` 约束（P1-3），非法值返回 422；
    - 非法状态转换返回 409，且**保留** ``resolved_at``：原先从 resolved 回退
      会把它清空，等于永久丢掉「这条告警何时被处理过」的审计事实（BUG-005）；
    - 状态变更写入审计日志（P1-4）。
    """
    alert = _active_alerts(db).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    previous_status = alert.status
    if update_data.status == previous_status:
        return alert  # 幂等：状态未变则不写库、不写审计

    allowed = ALLOWED_ALERT_TRANSITIONS.get(previous_status, set())
    if update_data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"不允许的状态转换：{previous_status} → {update_data.status}"
                f"（{previous_status} 只能转为 {'/'.join(sorted(allowed)) or '无'}）"
            ),
        )

    alert.status = update_data.status
    if update_data.status == ALERT_STATUS_RESOLVED:
        alert.resolved_at = datetime.now(timezone.utc)
    elif previous_status != ALERT_STATUS_RESOLVED:
        # 仅在「从未 resolved」时保持为空，避免抹掉历史处理时间
        alert.resolved_at = None

    db.commit()
    db.refresh(alert)

    audit.record(
        db,
        audit.AUDIT_ALERT_STATUS_CHANGED,
        actor=current_user,
        target=f"alert:{alert.id}",
        detail=f"{previous_status} → {alert.status}",
    )

    return alert


@router.delete("/alerts")
def clear_alerts(
    scope: Literal["all", "processed"] = Query(
        ..., description="'all' 清空全部, 'processed' 清空已处理"
    ),
    confirm: bool = Query(False, description="必须显式传 true，防止误操作"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """清空告警（**软删除** + 审计）"""
    _require_confirmation(confirm, "清空告警")

    query = _active_alerts(db)
    if scope == "processed":
        query = query.filter(Alert.status.in_(PROCESSED_ALERT_STATUSES))

    now = datetime.now(timezone.utc)
    count = query.update({Alert.deleted_at: now}, synchronize_session=False)
    db.commit()

    audit.record(
        db,
        audit.AUDIT_ALERTS_CLEARED,
        actor=current_user,
        target="alerts",
        detail=f"软删除告警（scope={scope}）",
        affected_rows=count,
    )
    return {"deleted": count, "scope": scope, "soft_deleted": True}
