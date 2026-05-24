"""Add composite indexes for tenders and proposals

Revision ID: 002
Revises: 001
Create Date: 2025-05-24

"""
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_tenders_status_deadline",
        "tenders",
        ["status", "deadline"],
        unique=False,
    )
    op.create_index(
        "ix_tender_proposals_tender_supplier",
        "tender_proposals",
        ["tender_id", "supplier_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tender_proposals_tender_supplier", table_name="tender_proposals")
    op.drop_index("ix_tenders_status_deadline", table_name="tenders")
