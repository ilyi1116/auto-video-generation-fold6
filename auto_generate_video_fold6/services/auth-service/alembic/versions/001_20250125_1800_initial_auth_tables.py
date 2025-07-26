"""Initial auth tables

Revision ID: 001
Revises: 
Create Date: 2025-01-25 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean(), default=False, nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False, nullable=False),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('website', sa.String(255), nullable=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('preferred_language', sa.String(10), default='en', nullable=False),
        sa.Column('timezone', sa.String(50), default='UTC', nullable=False),
        sa.Column('notification_preferences', sa.JSON(), default={}, nullable=False),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('login_count', sa.Integer(), default=0, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create indexes for users table
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])

    # Create user_sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('session_token', sa.String(255), nullable=False, unique=True),
        sa.Column('refresh_token', sa.String(255), nullable=False, unique=True),
        sa.Column('device_info', sa.JSON(), default={}, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for user_sessions table
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_session_token', 'user_sessions', ['session_token'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('idx_user_sessions_is_active', 'user_sessions', ['is_active'])

    # Create user_roles table
    op.create_table(
        'user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('permissions', sa.JSON(), default=[], nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # Create user_role_assignments table
    op.create_table(
        'user_role_assignments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('user_roles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assigned_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('user_id', 'role_id', name='unique_user_role'),
    )

    # Create password_reset_tokens table
    op.create_table(
        'password_reset_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for password_reset_tokens table
    op.create_index('idx_password_reset_tokens_user_id', 'password_reset_tokens', ['user_id'])
    op.create_index('idx_password_reset_tokens_token', 'password_reset_tokens', ['token'])
    op.create_index('idx_password_reset_tokens_expires_at', 'password_reset_tokens', ['expires_at'])

    # Create email_verification_tokens table
    op.create_table(
        'email_verification_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('token', sa.String(255), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', sa.JSON(), default={}, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),  # success, failure, error
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for audit_logs table
    op.create_index('idx_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('idx_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_logs_created_at', 'audit_logs', ['created_at'])
    op.create_index('idx_audit_logs_status', 'audit_logs', ['status'])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('audit_logs')
    op.drop_table('email_verification_tokens')
    op.drop_table('password_reset_tokens')
    op.drop_table('user_role_assignments')
    op.drop_table('user_roles')
    op.drop_table('user_sessions')
    op.drop_table('users')