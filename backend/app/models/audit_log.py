from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditLog(Base):
    """平台自身关键操作的审计记录（只增不改、不物理删除）。

    平台监控别人的登录行为，自身的关键操作同样必须留痕：
    管理员登录、创建管理员、修改密码、清空日志/告警、告警状态变更。
    见 docs/tech/14-评估与改进.md P1-4、10-安全分析.md SEC-12。
    """

    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("idx_audit_logs_action_created_at", "action", "created_at"),
    )

    id = Column(Integer, primary_key=True, index=True)
    #: 操作者（未登录场景如登录失败时为空）
    actor_id = Column(Integer)
    actor_username = Column(String(50))
    #: 动作标识，取值集中定义在 app/services/audit.py
    action = Column(String(50), nullable=False)
    #: 作用对象（用户名 / 接口资源名等）
    target = Column(String(100))
    #: 补充说明（**不得写入口令、token 等敏感信息**）
    detail = Column(String(500))
    #: 受影响行数（清空类操作）
    affected_rows = Column(Integer)
    created_at = Column(DateTime, default=_utcnow, index=True)
