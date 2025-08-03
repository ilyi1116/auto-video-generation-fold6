"""add keyword trends table

Revision ID: 20250803_001
Revises: 
Create Date: 2025-08-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250803_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create keyword_trends table
    op.create_table('keyword_trends',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=50), nullable=False),
        sa.Column('keyword', sa.String(length=500), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('search_volume', sa.Integer(), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('region', sa.String(length=10), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('score', sa.Integer(), nullable=True),
        sa.Column('change_percentage', sa.String(length=10), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_keyword_trends_id'), 'keyword_trends', ['id'], unique=False)
    op.create_index('ix_keyword_trends_platform_period', 'keyword_trends', ['platform', 'period'], unique=False)
    op.create_index('ix_keyword_trends_collected_at', 'keyword_trends', ['collected_at'], unique=False)
    op.create_index('ix_keyword_trends_rank', 'keyword_trends', ['rank'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_keyword_trends_rank', table_name='keyword_trends')
    op.drop_index('ix_keyword_trends_collected_at', table_name='keyword_trends')
    op.drop_index('ix_keyword_trends_platform_period', table_name='keyword_trends')
    op.drop_index(op.f('ix_keyword_trends_id'), table_name='keyword_trends')
    op.drop_table('keyword_trends')