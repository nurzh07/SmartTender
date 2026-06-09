"""DB triggers: updated_at auto-update and tender status audit log

Revision ID: 004
Revises: 003
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tender_audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tender_id", sa.Integer(), nullable=False),
        sa.Column("old_status", sa.String(), nullable=True),
        sa.Column("new_status", sa.String(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tender_id"], ["tenders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tender_audit_log_tender_id", "tender_audit_log", ["tender_id"])

    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for table in ("users", "tenders", "tender_proposals"):
        op.execute(f"""
            CREATE TRIGGER tr_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    op.execute("""
        CREATE OR REPLACE FUNCTION log_tender_status_change()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status IS DISTINCT FROM NEW.status THEN
                INSERT INTO tender_audit_log (tender_id, old_status, new_status)
                VALUES (OLD.id, OLD.status::text, NEW.status::text);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER tr_tenders_status_audit
        BEFORE UPDATE ON tenders
        FOR EACH ROW
        EXECUTE FUNCTION log_tender_status_change();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS tr_tenders_status_audit ON tenders;")
    op.execute("DROP FUNCTION IF EXISTS log_tender_status_change();")

    for table in ("users", "tenders", "tender_proposals"):
        op.execute(f"DROP TRIGGER IF EXISTS tr_{table}_updated_at ON {table};")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    op.drop_index("ix_tender_audit_log_tender_id", table_name="tender_audit_log")
    op.drop_table("tender_audit_log")
