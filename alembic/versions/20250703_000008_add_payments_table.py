"""Add payments table for Stripe integration

Revision ID: 008
Revises: 007
Create Date: 2026-07-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payments table if it doesn't exist
    from sqlalchemy import inspect
    
    conn = op.get_bind()
    inspector = inspect(conn)
    
    if 'payments' not in inspector.get_table_names():
        op.create_table(
            'payments',
            sa.Column('id', sa.Integer(), primary_key=True, index=True),
            sa.Column('tender_id', sa.Integer(), sa.ForeignKey('tenders.id'), nullable=False),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('amount', sa.Numeric(10, 2), nullable=False),
            sa.Column('currency', sa.String(3), default='KZT', nullable=False),
            sa.Column('status', sa.String(50), default='pending', nullable=False),
            sa.Column('stripe_payment_intent_id', sa.String(255), nullable=True, unique=True),
            sa.Column('stripe_client_secret', sa.String(500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('NOW()'), nullable=True),
        )
        
        # Add payment_pending status to tender status enum if needed
        # This is handled separately in the tender status migration


def downgrade() -> None:
    op.drop_table('payments')
