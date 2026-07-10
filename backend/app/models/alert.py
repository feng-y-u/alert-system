from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        Index("idx_alerts_username_alert_type_status", "username", "alert_type", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    log_id = Column(Integer, ForeignKey("login_logs.id"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False)
    alert_message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)

    # 关联关系
    log = relationship("LoginLog", backref="alerts")