from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models.alert import Alert
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertResponse, AlertUpdate

router = APIRouter()


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    status: Optional[str] = Query(None, description="Filter by status: pending/acknowledged/resolved"),
    severity: Optional[str] = Query(None, description="Filter by severity: low/medium/high"),
    username: Optional[str] = Query(None, description="Filter by username"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询告警列表"""
    query = db.query(Alert)

    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
    if username:
        query = query.filter(Alert.username == username)

    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "items": alerts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
def get_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个告警详情"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.put("/alerts/{alert_id}", response_model=AlertResponse)
def update_alert(
    alert_id: int,
    update_data: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """更新告警状态"""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # 更新状态
    if update_data.status:
        alert.status = update_data.status
        if update_data.status == "resolved":
            alert.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(alert)
    return alert


@router.delete("/alerts")
def clear_alerts(
    scope: Literal["all", "processed"] = Query(..., description="'all' 清空全部, 'processed' 清空已处理"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """清空告警"""
    query = db.query(Alert)
    if scope == "processed":
        query = query.filter(Alert.status.in_(["acknowledged", "resolved"]))

    count = query.delete(synchronize_session=False)
    db.commit()
    return {"deleted": count, "scope": scope}
