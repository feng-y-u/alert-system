from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Column, Computed, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def pending_dedup_expression():
    """未处理告警去重键的生成列表达式。

    pending 且未软删除时取 ``username#alert_type``，其余情况为 NULL。
    唯一索引允许多个 NULL，因此「同一用户 + 同类型只允许一条 pending 告警」
    由数据库保证，而不是只靠应用层的一次 SELECT —— 后者在并发下会失效
    （两个检测任务都查到「没有 pending 告警」，于是各插一条，见 BUG-002）。

    用 SQLAlchemy 的 ``concat()`` 而不是 ``text("CONCAT(...)")``：
    MySQL 编译为 ``concat(a, b, c)``，SQLite 编译为 ``a || b || c``，
    单一定义同时适配生产库与测试库。
    """
    return sa.case(
        (
            sa.and_(
                sa.column("status") == sa.literal("pending"),
                sa.column("deleted_at").is_(None),
            ),
            sa.column("username")
            .concat(sa.literal("#"))
            .concat(sa.column("alert_type")),
        ),
        else_=None,
    )


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        Index("idx_alerts_username_alert_type_status", "username", "alert_type", "status"),
        Index("uq_alerts_pending_dedup", "pending_dedup_key", unique=True),
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
    #: 生成列（STORED）：并发去重的唯一约束载体。值由数据库计算，
    #: 应用层不写入（``Computed`` 会让 SQLAlchemy 把该列排除在 INSERT 之外）。
    pending_dedup_key = Column(
        String(120),
        Computed(pending_dedup_expression(), persisted=True),
        nullable=True,
    )

    # 关联关系
    log = relationship("LoginLog", backref="alerts")