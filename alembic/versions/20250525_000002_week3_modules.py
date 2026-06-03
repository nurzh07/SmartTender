"""Week 3: approval, notifications, reports, supplier ratings

Revision ID: 003
Revises: 002
"""
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_chat_id", sa.String(), nullable=True))
    op.add_column("tenders", sa.Column("external_id", sa.String(), nullable=True))
    op.add_column("tenders", sa.Column("approval_status", sa.String(), server_default="draft"))
    op.create_index("ix_tenders_external_id", "tenders", ["external_id"], unique=False)

    op.create_table(
        "approval_workflow",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tender_id", sa.Integer(), nullable=False),
        sa.Column("approver_id", sa.Integer(), nullable=True),
        sa.Column("step", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "approved", "rejected", name="approvalstatus"),
            nullable=False,
        ),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["approver_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tender_id"], ["tenders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_approval_workflow_tender_id", "approval_workflow", ["tender_id"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "tender_published",
                "approval_approved",
                "approval_rejected",
                "deadline_reminder",
                "tender_awarded",
                "password_reset",
                "report_ready",
                name="notificationtype",
            ),
            nullable=False,
        ),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_read", sa.Boolean(), default=False),
        sa.Column(
            "channel",
            sa.Enum("email", "telegram", "in_app", name="notificationchannel"),
            nullable=True,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "report_type",
            sa.Enum(
                "monthly_tenders_pdf",
                "supplier_ratings_excel",
                "budget_analytics",
                name="reporttype",
            ),
            nullable=False,
        ),
        sa.Column("period", sa.String(), nullable=False),
        sa.Column("file_url", sa.String(), nullable=True),
        sa.Column("generated_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "supplier_ratings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("tender_id", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("delivery_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("avg_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["supplier_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["tender_id"], ["tenders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_supplier_ratings_supplier_id", "supplier_ratings", ["supplier_id"])


def downgrade() -> None:
    op.drop_index("ix_supplier_ratings_supplier_id", "supplier_ratings")
    op.drop_table("supplier_ratings")
    op.drop_table("reports")
    op.drop_index("ix_notifications_user_id", "notifications")
    op.drop_table("notifications")
    op.drop_index("ix_approval_workflow_tender_id", "approval_workflow")
    op.drop_table("approval_workflow")
    op.drop_index("ix_tenders_external_id", "tenders")
    op.drop_column("tenders", "approval_status")
    op.drop_column("tenders", "external_id")
    op.drop_column("users", "telegram_chat_id")
    op.execute("DROP TYPE IF EXISTS approvalstatus")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS notificationchannel")
    op.execute("DROP TYPE IF EXISTS reporttype")
