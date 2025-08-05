from databases import Database
from sqlalchemy import (
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

from .config import get_settings

settings = get_settings()

# Database connection
database = Database(settings.database_url)
engine = create_engine(settings.database_url)
metadata = MetaData()

# Voice models table
voice_models = Table(
    "voice_models",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text),
    Column("model_type", String(50), nullable=False, default="tacotron2"),
    Column("language", String(10), nullable=False, default="en"),
    Column("status", String(20), nullable=False, default="training"),  # training, ready, failed
    Column("model_path", String(500)),  # S3 path to model files
    Column("config_data", Text),  # JSON config for model
    Column("training_data_size", Integer, default=0),
    Column("training_duration", Float),  # Training time in seconds
    Column("quality_score", Float),  # Model quality metric
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)

# Synthesis jobs table
synthesis_jobs = Table(
    "synthesis_jobs",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("model_id", Integer, ForeignKey("voice_models.id"), nullable=False),
    Column("text", Text, nullable=False),
    Column(
        "status", String(20), nullable=False, default="pending"
    ),  # pending, processing, completed, failed
    Column("audio_url", String(500)),  # S3 URL to generated audio
    Column("audio_duration", Float),  # Duration in seconds
    Column("synthesis_params", Text),  # JSON parameters used
    Column("error_message", Text),
    Column("processing_time", Float),  # Time taken in seconds
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("completed_at", DateTime(timezone=True)),
)

# Model usage statistics
model_usage_stats = Table(
    "model_usage_stats",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("model_id", Integer, ForeignKey("voice_models.id"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
    Column("synthesis_count", Integer, default=0),
    Column("total_characters", Integer, default=0),
    Column("total_audio_duration", Float, default=0.0),
    Column("last_used_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)
