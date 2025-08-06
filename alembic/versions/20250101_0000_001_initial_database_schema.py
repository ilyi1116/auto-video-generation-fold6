"""Initial database schema

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema with extensions, tables, and indexes."""

    # Create extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # Users table (基礎認證系統)
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("username", sa.String(100), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("plan_type", sa.String(50), default="free"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )

    # Video projects table
    op.create_table(
        "video_projects",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", sa.String(50), default="draft"),
        sa.Column("settings", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Keywords table
    op.create_table(
        "keywords",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("keyword", sa.String(255), unique=True, nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("trending_score", sa.Integer, default=0),
        sa.Column("search_volume", sa.Integer, default=0),
        sa.Column("last_analyzed", sa.TIMESTAMP(timezone=True)),
        sa.Column("metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )

    # Project keywords association table
    op.create_table(
        "project_keywords",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("keyword_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weight", sa.Float, default=1.0),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("project_id", "keyword_id"),
    )

    # Scripts table
    op.create_table(
        "scripts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("style", sa.String(100)),
        sa.Column("duration_seconds", sa.Integer),
        sa.Column("ai_model", sa.String(100)),
        sa.Column("generation_params", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(50), default="generated"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"], ondelete="CASCADE"),
    )

    # Voice synthesis table
    op.create_table(
        "voice_synthesis",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("script_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("voice_style", sa.String(100)),
        sa.Column("audio_file_path", sa.String(500)),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("ai_service", sa.String(100)),
        sa.Column("synthesis_params", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"], ondelete="CASCADE"),
    )

    # Image generation table
    op.create_table(
        "image_generation",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt", sa.Text, nullable=False),
        sa.Column("style", sa.String(100)),
        sa.Column("aspect_ratio", sa.String(20)),
        sa.Column("image_file_path", sa.String(500)),
        sa.Column("ai_service", sa.String(100)),
        sa.Column("generation_params", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"], ondelete="CASCADE"),
    )

    # Video generation table
    op.create_table(
        "video_generation",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("script_id", postgresql.UUID(as_uuid=True)),
        sa.Column("voice_id", postgresql.UUID(as_uuid=True)),
        sa.Column("video_file_path", sa.String(500)),
        sa.Column("thumbnail_path", sa.String(500)),
        sa.Column("duration_seconds", sa.Float),
        sa.Column("resolution", sa.String(20)),
        sa.Column("aspect_ratio", sa.String(20)),
        sa.Column("file_size_mb", sa.Float),
        sa.Column("processing_params", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["script_id"], ["scripts.id"]),
        sa.ForeignKeyConstraint(["voice_id"], ["voice_synthesis.id"]),
    )

    # Social platforms table
    op.create_table(
        "social_platforms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_user_id", sa.String(255)),
        sa.Column("access_token", sa.Text),
        sa.Column("refresh_token", sa.Text),
        sa.Column("token_expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("account_info", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column(
            "updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "platform"),
    )

    # Publish schedule table
    op.create_table(
        "publish_schedule",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("scheduled_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("tags", postgresql.ARRAY(sa.Text)),
        sa.Column("privacy_setting", sa.String(50), default="public"),
        sa.Column("status", sa.String(50), default="scheduled"),
        sa.Column("platform_post_id", sa.String(255)),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("error_message", sa.Text),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["platform_id"], ["social_platforms.id"], ondelete="CASCADE"),
    )

    # Trend analysis table
    op.create_table(
        "trend_analysis",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("keyword_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("analysis_date", sa.Date, nullable=False),
        sa.Column("view_count", sa.BigInteger, default=0),
        sa.Column("like_count", sa.BigInteger, default=0),
        sa.Column("share_count", sa.BigInteger, default=0),
        sa.Column("engagement_rate", sa.Float, default=0),
        sa.Column("trending_score", sa.Integer, default=0),
        sa.Column("analysis_data", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["keyword_id"], ["keywords.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("keyword_id", "platform", "analysis_date"),
    )

    # User credits table
    op.create_table(
        "user_credits",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column("total_credits", sa.Integer, default=0),
        sa.Column("used_credits", sa.Integer, default=0),
        sa.Column("bonus_credits", sa.Integer, default=0),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "last_updated", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    # Credit transactions table
    op.create_table(
        "credit_transactions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True)),
        sa.Column("transaction_type", sa.String(50), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("description", sa.String(255)),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["video_projects.id"]),
    )

    # System tasks table
    op.create_table(
        "system_tasks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("task_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("priority", sa.Integer, default=0),
        sa.Column("attempts", sa.Integer, default=0),
        sa.Column("max_attempts", sa.Integer, default=3),
        sa.Column("task_data", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("result", postgresql.JSONB),
        sa.Column("error_message", sa.Text),
        sa.Column("scheduled_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column(
            "created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")
        ),
    )

    # Create indexes for performance
    op.create_index("idx_video_projects_user_id", "video_projects", ["user_id"])
    op.create_index("idx_video_projects_status", "video_projects", ["status"])
    op.create_index(
        "idx_keywords_trending_score",
        "keywords",
        ["trending_score"],
        postgresql_using="btree",
        postgresql_ops={"trending_score": "DESC"},
    )
    op.create_index("idx_scripts_project_id", "scripts", ["project_id"])
    op.create_index("idx_voice_synthesis_script_id", "voice_synthesis", ["script_id"])
    op.create_index("idx_image_generation_project_id", "image_generation", ["project_id"])
    op.create_index("idx_video_generation_project_id", "video_generation", ["project_id"])
    op.create_index("idx_publish_schedule_scheduled_time", "publish_schedule", ["scheduled_time"])
    op.create_index(
        "idx_trend_analysis_date",
        "trend_analysis",
        ["analysis_date"],
        postgresql_using="btree",
        postgresql_ops={"analysis_date": "DESC"},
    )
    op.create_index("idx_system_tasks_status", "system_tasks", ["status"])
    op.create_index("idx_system_tasks_scheduled_at", "system_tasks", ["scheduled_at"])

    # Create trigger function for updating updated_at columns
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """
    )

    # Create triggers
    op.execute(
        """
        CREATE TRIGGER update_video_projects_updated_at
        BEFORE UPDATE ON video_projects
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_social_platforms_updated_at
        BEFORE UPDATE ON social_platforms
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
    )


def downgrade() -> None:
    """Drop all tables and extensions."""

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_video_projects_updated_at ON video_projects")
    op.execute("DROP TRIGGER IF EXISTS update_social_platforms_updated_at ON social_platforms")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")

    # Drop indexes
    op.drop_index("idx_system_tasks_scheduled_at")
    op.drop_index("idx_system_tasks_status")
    op.drop_index("idx_trend_analysis_date")
    op.drop_index("idx_publish_schedule_scheduled_time")
    op.drop_index("idx_video_generation_project_id")
    op.drop_index("idx_image_generation_project_id")
    op.drop_index("idx_voice_synthesis_script_id")
    op.drop_index("idx_scripts_project_id")
    op.drop_index("idx_keywords_trending_score")
    op.drop_index("idx_video_projects_status")
    op.drop_index("idx_video_projects_user_id")

    # Drop tables in reverse order of dependencies
    op.drop_table("system_tasks")
    op.drop_table("credit_transactions")
    op.drop_table("user_credits")
    op.drop_table("trend_analysis")
    op.drop_table("publish_schedule")
    op.drop_table("social_platforms")
    op.drop_table("video_generation")
    op.drop_table("image_generation")
    op.drop_table("voice_synthesis")
    op.drop_table("scripts")
    op.drop_table("project_keywords")
    op.drop_table("keywords")
    op.drop_table("video_projects")
    op.drop_table("users")

    # Drop extensions (optional - usually kept for other databases)
    # op.execute('DROP EXTENSION IF EXISTS "pg_trgm"')
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
