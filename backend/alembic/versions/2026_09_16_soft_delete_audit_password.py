"""软删除、审计日志与密码策略

Revision ID: 2026_09_16_soft_delete_audit_password
Revises: 2026_07_10_add_log_id_to_alerts
Create Date: 2026-09-16 00:00:00.000000

对应 docs/tech/14-评估与改进.md：

- P1-3：把存量 ``login_status`` 的 ``failed``/``fail`` 归一化为 ``failure``，
  消除「数据能入库但按失败筛不出来」的契约破损；
- P1-4：``login_logs``/``alerts`` 增加 ``deleted_at`` 软删除标记；
  新增 ``audit_logs`` 审计表；``alerts.log_id`` 外键改为 ``ON DELETE SET NULL``，
  避免删除日志时被 RESTRICT 拦住；
- P1-6：``users.must_change_password`` 支持「初始口令强制修改」。
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2026_09_16_soft_delete_audit_password'
down_revision: Union[str, None] = '2026_07_10_add_log_id_to_alerts'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── P1-6：初始密码强制修改标记（NOT NULL 必须给 server_default，否则非空表升级失败）
    op.add_column(
        'users',
        sa.Column(
            'must_change_password',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('0'),
        ),
    )

    # ── P1-4：软删除标记
    op.add_column('login_logs', sa.Column('deleted_at', sa.DateTime(), nullable=True))
    op.add_column('alerts', sa.Column('deleted_at', sa.DateTime(), nullable=True))

    # ── P1-4：审计日志表
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('actor_username', sa.String(length=50), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('target', sa.String(length=100), nullable=True),
        sa.Column('detail', sa.String(length=500), nullable=True),
        sa.Column('affected_rows', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_audit_logs_id'), 'audit_logs', ['id'], unique=False)
    op.create_index(
        'idx_audit_logs_action_created_at', 'audit_logs', ['action', 'created_at']
    )

    # ── P1-4：外键改为 ON DELETE SET NULL（删除日志时解除告警引用而不是报错）
    op.drop_constraint('fk_alerts_log_id_login_logs', 'alerts', type_='foreignkey')
    op.create_foreign_key(
        'fk_alerts_log_id_login_logs',
        'alerts',
        'login_logs',
        ['log_id'],
        ['id'],
        ondelete='SET NULL',
    )

    # ── P1-3：存量词表归一化（failed/fail → failure）
    op.execute(
        "UPDATE login_logs SET login_status = 'failure' "
        "WHERE login_status IN ('failed', 'fail')"
    )


def downgrade() -> None:
    op.drop_constraint('fk_alerts_log_id_login_logs', 'alerts', type_='foreignkey')
    op.create_foreign_key(
        'fk_alerts_log_id_login_logs',
        'alerts',
        'login_logs',
        ['log_id'],
        ['id'],
    )

    op.drop_index('idx_audit_logs_action_created_at', table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_id'), table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_column('alerts', 'deleted_at')
    op.drop_column('login_logs', 'deleted_at')
    op.drop_column('users', 'must_change_password')
