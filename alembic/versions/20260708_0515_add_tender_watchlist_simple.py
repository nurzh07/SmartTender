"""add tender watchlist table

Revision ID: 20260708_0515
Revises: 008
Create Date: 2026-07-08 05:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260708_0515'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tender_watchlist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('tender_id', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tender_watchlist_id'), 'tender_watchlist', ['id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_tender_watchlist_id'), table_name='tender_watchlist')
    op.drop_table('tender_watchlist')
