from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    alert_type = Column(String(50), nullable=False)
    alert_message = Column(String(500), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
