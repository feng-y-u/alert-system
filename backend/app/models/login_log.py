from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    login_time = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(String(500))
    login_status = Column(String(20), nullable=False)
    location = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
