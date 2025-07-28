import databases
import sqlalchemy
from app.config import settings
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
)
from sqlalchemy.sql import func

# Database connection
database = databases.Database(settings.database_url)
metadata = MetaData()

# Create engine
engine = create_engine(settings.database_url)

# Voice data files table
voice_files = Table(
    "voice_files",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("filename", String(255), nullable=False),
    Column("original_filename", String(255), nullable=False),
    Column("file_path", String(512), nullable=False),
    Column("s3_key", String(512), nullable=True),
    Column("file_size", Integer, nullable=False),
    Column("mime_type", String(100), nullable=False),
    Column("duration", Float, nullable=True),
    Column("sample_rate", Integer, nullable=True),
    Column("channels", Integer, nullable=True),
    Column("status", String(50), default="pending"),  # pending, processing, processed, failed
    Column("metadata", Text, nullable=True),  # JSON metadata
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
)

# Processing jobs table
processing_jobs = Table(
    "processing_jobs",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("voice_file_id", Integer, ForeignKey("voice_files.id"), nullable=False),
    Column("job_type", String(50), nullable=False),  # preprocessing, training, inference
    Column("status", String(50), default="pending"),  # pending, running, completed, failed
    Column("progress", Integer, default=0),  # 0-100
    Column("result_data", Text, nullable=True),  # JSON result data
    Column("error_message", Text, nullable=True),
    Column("celery_task_id", String(255), nullable=True),
    Column("started_at", DateTime, nullable=True),
    Column("completed_at", DateTime, nullable=True),
    Column("created_at", DateTime, default=func.now()),
    Column("updated_at", DateTime, default=func.now(), onupdate=func.now()),
)
