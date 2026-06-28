"""add worker heartbeats table

Revision ID: 541985d21bba
Revises: 001
Create Date: 2026-06-28
"""
from alembic import op
import sqlalchemy as sa

revision = '541985d21bba'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'worker_heartbeats',
        sa.Column('worker_id', sa.String(50), primary_key=True),
        sa.Column('last_seen', sa.DateTime, server_default=sa.func.now()),
        sa.Column('status', sa.String(20), server_default='alive'),
    )

def downgrade():
    op.drop_table('worker_heartbeats')
