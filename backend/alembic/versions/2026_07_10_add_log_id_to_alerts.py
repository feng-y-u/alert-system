"""add log_id to alerts and create indexes

Revision ID: 2026_07_10_add_log_id_to_alerts
Revises: 2e7a3f8b1c4d
Create Date: 2026-07-10 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2026_07_10_add_log_id_to_alerts'
down_revision: Union[str, None] = '2e7a3f8b1c4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 添加 log_id 字段到 alerts 表
    op.add_column('alerts', sa.Column('log_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_alerts_log_id_login_logs',
        'alerts', 'login_logs',
        ['log_id'], ['id']
    )

    # 创建 alerts 表索引
    op.create_index(
        'idx_alerts_username_alert_type_status',
        'alerts',
        ['username', 'alert_type', 'status']
    )

    # 创建 login_logs 表复合索引
    op.create_index(
        'idx_login_logs_username_login_time',
        'login_logs',
        ['username', 'login_time']
    )


def downgrade() -> None:
    op.drop_index('idx_login_logs_username_login_time', table_name='login_logs')
    op.drop_index('idx_alerts_username_alert_type_status', table_name='alerts')
    op.drop_constraint('fk_alerts_log_id_login_logs', 'alerts', type_='foreignkey')
    op.drop_column('alerts', 'log_id')