"""create jobs table

Revision ID: 001
Revises: 
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('payload', sa.Text, nullable=False),
        sa.Column('retry_count', sa.Integer, server_default='0'),
        sa.Column('max_retries', sa.Integer, server_default='3'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('error_message', sa.Text, nullable=True),
    )

def downgrade():
    op.drop_table('jobs')
