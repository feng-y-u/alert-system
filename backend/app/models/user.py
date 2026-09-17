from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="admin")
    is_active = Column(Boolean, default=True)
    #: 首次登录（初始口令）后必须修改密码，否则除改密接口外一律 403
    must_change_password = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
