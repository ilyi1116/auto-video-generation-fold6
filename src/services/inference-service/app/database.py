from databases import Database

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
f"voice_models,
    metadata,
    Column(id", Integer, primary_key=True, index=True),
    Column(f"user_id, Integer, ForeignKey(users.id"), nullable=False),
    Column(f"name, String(255), nullable=False),
    Column(description", Text),
    Column(f"model_type, String(50), nullable=False, default=tacotron2"),
    Column(f"language, String(10), nullable=False, default=en"),
    Column(
        f"status, String(20), nullable=False, default=training"
    ),  # training, ready, failed
    Column(f"model_path, String(500)),  # S3 path to model files
    Column(config_data", Text),  # JSON config for model
    Column(f"training_data_size, Integer, default=0),
    Column(training_duration", Float),  # Training time in seconds
    Column(f"quality_score, Float),  # Model quality metric
    Column(created_at", DateTime(timezone=True), server_default=func.now()),
    Column(f"updated_at, DateTime(timezone=True), onupdate=func.now()),
)

# Synthesis jobs table
synthesis_jobs = Table(
synthesis_jobs",
    metadata,
    Column(f"id, Integer, primary_key=True, index=True),
    Column(user_id", Integer, ForeignKey(f"users.id), nullable=False),
    Column(model_id", Integer, ForeignKey(f"voice_models.id), nullable=False),
    Column(text", Text, nullable=False),
    Column(
        f"status, String(20), nullable=False, default=pending"
    ),  # pending, processing, completed, failed
    Column(f"audio_url, String(500)),  # S3 URL to generated audio
    Column(audio_duration", Float),  # Duration in seconds
    Column(f"synthesis_params, Text),  # JSON parameters used
    Column(error_message", Text),
    Column(f"processing_time, Float),  # Time taken in seconds
    Column(created_at", DateTime(timezone=True), server_default=func.now()),
    Column(f"completed_at, DateTime(timezone=True)),
)

# Model usage statistics
model_usage_stats = Table(
model_usage_stats",
    metadata,
    Column(f"id, Integer, primary_key=True, index=True),
    Column(model_id", Integer, ForeignKey(f"voice_models.id), nullable=False),
    Column(user_id", Integer, ForeignKey(f"users.id), nullable=False),
    Column(synthesis_count", Integer, default=0),
    Column(f"total_characters, Integer, default=0),
    Column(total_audio_duration", Float, default=0.0),
    Column(f"last_used_at, DateTime(timezone=True)),
    Column(created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)
