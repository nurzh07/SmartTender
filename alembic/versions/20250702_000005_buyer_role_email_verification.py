"""Rename procurement_manager to buyer; add email verification flag

Revision ID: 005
Revises: 004
"""
import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME VALUE 'procurement_manager' TO 'buyer'")
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    op.alter_column("users", "is_verified", server_default=sa.text("false"))


def downgrade() -> None:
    op.drop_column("users", "is_verified")
    op.execute("ALTER TYPE userrole RENAME VALUE 'buyer' TO 'procurement_manager'")
