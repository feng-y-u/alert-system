"""未处理告警去重唯一约束（BUG-002）

Revision ID: 2026_09_18_alert_dedup_uq
Revises: 2026_09_16_soft_delete_audit
Create Date: 2026-09-18 00:00:00.000000

⚠️ revision id 必须 ≤ 32 字符（``alembic_version.version_num`` 是 ``VARCHAR(32)``），
本 id 为 27 字符。

背景：告警去重（``should_create_alert``）是「先 SELECT 再 INSERT」的 check-then-act，
两步之间没有互斥。两条并发到达的登录日志各自投递一次检测任务，两个任务都可能
查到「没有 pending 告警」，于是各插一条 —— 同一用户同类型出现重复 pending 告警，
去重承诺失效，邮件与 SSE 也会重复推送。

修复方式：增加生成列 + 唯一索引，把「同一 (username, alert_type) 只允许一条
未软删除的 pending 告警」下沉到数据库。生成列在 pending 且未软删除时取
``username#alert_type``，其余情况为 NULL（唯一索引允许多个 NULL，所以
acknowledged / resolved / 已软删除都不占用槽位，与既有去重语义一致）。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql, sqlite
from sqlalchemy.schema import CreateColumn

from app.models.alert import pending_dedup_expression

revision: str = '2026_09_18_alert_dedup_uq'
down_revision: Union[str, None] = '2026_09_16_soft_delete_audit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _generated_column_ddl(bind) -> str:
    """按实际方言渲染生成列定义。

    MySQL 编译为 ``concat(...)``，SQLite 编译为 ``||``；
    直接写 ``text("CONCAT(...)")`` 会让 SQLite 上的测试库建表失败。
    """
    column = sa.Column(
        'pending_dedup_key',
        sa.String(120),
        sa.Computed(pending_dedup_expression(), persisted=True),
        nullable=True,
    )
    dialect = sqlite.dialect() if bind.dialect.name == 'sqlite' else mysql.dialect()
    return str(CreateColumn(column).compile(dialect=dialect))


def upgrade() -> None:
    bind = op.get_bind()

    # ── 1. 存量重复 pending 告警：同 (username, alert_type) 只保留最早一条 ──
    # 「最早」= 最先被发现的那次异常，保留它并把其余标记为「已确认」，
    # 而不是物理删除（告警是审计证据）。
    groups = bind.execute(
        sa.text(
            """
            SELECT username, alert_type FROM alerts
            WHERE status = 'pending' AND deleted_at IS NULL
            GROUP BY username, alert_type
            HAVING COUNT(*) > 1
            """
        )
    ).fetchall()

    merged = 0
    for username, alert_type in groups:
        rows = bind.execute(
            sa.text(
                """
                SELECT id FROM alerts
                WHERE username = :username AND alert_type = :alert_type
                  AND status = 'pending' AND deleted_at IS NULL
                ORDER BY created_at ASC, id ASC
                """
            ),
            {"username": username, "alert_type": alert_type},
        ).fetchall()
        for (stale_id,) in rows[1:]:
            bind.execute(
                sa.text(
                    "UPDATE alerts SET status = 'acknowledged' WHERE id = :stale_id"
                ),
                {"stale_id": stale_id},
            )
            merged += 1
    if merged:
        print(f"[migrate] 已归并重复的 pending 告警：{merged} 条（标记为 acknowledged）")

    # ── 2. 生成列 + 唯一索引 ──
    op.execute(
        f"ALTER TABLE alerts ADD COLUMN {_generated_column_ddl(bind)}"
    )
    op.create_index(
        'uq_alerts_pending_dedup', 'alerts', ['pending_dedup_key'], unique=True
    )


def downgrade() -> None:
    op.drop_index('uq_alerts_pending_dedup', table_name='alerts')
    op.drop_column('alerts', 'pending_dedup_key')
