"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create departments table
    op.create_table(
        'departments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('budget_limit', sa.Numeric(15, 2), nullable=True),
        sa.Column('head_user_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_departments_id'), 'departments', ['id'], unique=False)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', sa.Enum('superadmin', 'procurement_manager', 'department_head', 'employee', 'supplier', name='userrole'), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('department_id', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['department_id'], ['departments.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create categories table
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_id'), 'categories', ['id'], unique=False)

    # Create tenders table
    op.create_table(
        'tenders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('budget', sa.Numeric(15, 2), nullable=False),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.Enum('draft', 'published', 'evaluation', 'awarded', 'closed', name='tenderstatus'), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tenders_created_by'), 'tenders', ['created_by'], unique=False)
    op.create_index(op.f('ix_tenders_id'), 'tenders', ['id'], unique=False)

    # Create tender_proposals table
    op.create_table(
        'tender_proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tender_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Numeric(15, 2), nullable=False),
        sa.Column('delivery_days', sa.Integer(), nullable=False),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'accepted', 'rejected', name='proposalstatus'), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['supplier_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['tender_id'], ['tenders.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tender_proposals_id'), 'tender_proposals', ['id'], unique=False)
    op.create_index(op.f('ix_tender_proposals_supplier_id'), 'tender_proposals', ['supplier_id'], unique=False)
    op.create_index(op.f('ix_tender_proposals_tender_id'), 'tender_proposals', ['tender_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tender_proposals_tender_id'), table_name='tender_proposals')
    op.drop_index(op.f('ix_tender_proposals_supplier_id'), table_name='tender_proposals')
    op.drop_index(op.f('ix_tender_proposals_id'), table_name='tender_proposals')
    op.drop_table('tender_proposals')
    
    op.drop_index(op.f('ix_tenders_id'), table_name='tenders')
    op.drop_index(op.f('ix_tenders_created_by'), table_name='tenders')
    op.drop_table('tenders')
    
    op.drop_index(op.f('ix_categories_id'), table_name='categories')
    op.drop_table('categories')
    
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_departments_id'), table_name='departments')
    op.drop_table('departments')
    
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS tenderstatus')
    op.execute('DROP TYPE IF EXISTS proposalstatus')
