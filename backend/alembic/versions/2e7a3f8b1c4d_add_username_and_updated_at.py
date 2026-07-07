"""add username and updated_at to alerts, add updated_at to users and login_logs

Revision ID: 2e7a3f8b1c4d
Revises: 59f48e69b011
Create Date: 2026-07-07 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2e7a3f8b1c4d'
down_revision: Union[str, None] = '59f48e69b011'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # alerts: drop user_id, add username + updated_at
    op.drop_index('ix_alerts_user_id', table_name='alerts')
    op.drop_column('alerts', 'user_id')
    op.add_column('alerts', sa.Column('username', sa.String(length=50), nullable=False))
    op.create_index(op.f('ix_alerts_username'), 'alerts', ['username'], unique=False)
    op.add_column('alerts', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # users: add updated_at
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # login_logs: add updated_at
    op.add_column('login_logs', sa.Column('updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # login_logs: drop updated_at
    op.drop_column('login_logs', 'updated_at')

    # users: drop updated_at
    op.drop_column('users', 'updated_at')

    # alerts: drop username + updated_at, restore user_id
    op.drop_index(op.f('ix_alerts_username'), table_name='alerts')
    op.drop_column('alerts', 'username')
    op.drop_column('alerts', 'updated_at')
    op.add_column('alerts', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_alerts_user_id'), 'alerts', ['user_id'], unique=False)