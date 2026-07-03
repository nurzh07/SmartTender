"""Add Telegram fields to users

Revision ID: 006
Revises: 005
Create Date: 2026-07-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Telegram fields to users table if they don't exist
    from alembic import op
    import sqlalchemy as sa
    from sqlalchemy import inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'telegram_chat_id' not in columns:
        op.add_column('users', sa.Column('telegram_chat_id', sa.String(), nullable=True))
    
    if 'telegram_connect_code' not in columns:
        op.add_column('users', sa.Column('telegram_connect_code', sa.String(), nullable=True))


def downgrade() -> None:
    # Remove Telegram fields from users table
    op.drop_column('users', 'telegram_connect_code')
    op.drop_column('users', 'telegram_chat_id')
