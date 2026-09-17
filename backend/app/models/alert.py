from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        Index("idx_alerts_username_alert_type_status", "username", "alert_type", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    # ondelete="SET NULL"：删除日志时解除告警引用，而不是被 RESTRICT 拦住
    log_id = Column(
        Integer,
        ForeignKey("login_logs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    alert_type = Column(String(50), nullable=False)
    alert_message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    resolved_at = Column(DateTime)
    #: 软删除标记：销毁接口只打标记，不再物理删除（保护审计证据）
    deleted_at = Column(DateTime)

    # 关联关系
    log = relationship("LoginLog", backref="alerts")