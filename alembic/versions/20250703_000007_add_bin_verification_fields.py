"""Add BIN verification fields to users

Revision ID: 007
Revises: 006
Create Date: 2026-07-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add BIN verification fields to users table if they don't exist
    from sqlalchemy import inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'bin' not in columns:
        op.add_column('users', sa.Column('bin', sa.String(12), nullable=True, index=True))
    
    if 'bin_verified' not in columns:
        op.add_column('users', sa.Column('bin_verified', sa.Boolean(), nullable=False, server_default='false'))
    
    if 'company_official_name' not in columns:
        op.add_column('users', sa.Column('company_official_name', sa.String(), nullable=True))
    
    if 'company_registration_date' not in columns:
        op.add_column('users', sa.Column('company_registration_date', sa.Date(), nullable=True))
    
    if 'company_status' not in columns:
        op.add_column('users', sa.Column('company_status', sa.String(), nullable=True))
    
    if 'bin_verified_at' not in columns:
        op.add_column('users', sa.Column('bin_verified_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove BIN verification fields from users table
    op.drop_column('users', 'bin_verified_at')
    op.drop_column('users', 'company_status')
    op.drop_column('users', 'company_registration_date')
    op.drop_column('users', 'company_official_name')
    op.drop_column('users', 'bin_verified')
    op.drop_column('users', 'bin')
